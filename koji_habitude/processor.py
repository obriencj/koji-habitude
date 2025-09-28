"""
koji_habitude.processor

Core processing engine for synchronizing koji objects with a hub instance.
Handles the read/compare/write cycle in chunks with multicall optimization.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""


# Vibe-Coding State: AI Assisted, Mostly Human


from dataclasses import dataclass
from enum import Enum
from typing import Iterator, Dict, List, Any, Optional, Tuple, Callable
import logging

from koji import ClientSession, VirtualCall

from .koji import multicall
from .models import BaseKey, Base, ChangeReport
from .solver import Solver


logger = logging.getLogger(__name__)


class ProcessorState(Enum):
    """
    Processor state machine for managing the read/compare/apply cycle.

    State transitions:
    READY_CHUNK → READY_READ → READY_COMPARE → READY_APPLY → READY_CHUNK
    Any state → BROKEN (on error)
    READY_CHUNK → EXHAUSTED (when stream empty)
    """
    READY_CHUNK = "ready-chunk"      # Ready to load new chunk
    READY_READ = "ready-read"        # Ready to fetch koji data
    READY_COMPARE = "ready-compare"  # Ready to analyze differences
    READY_APPLY = "ready-apply"      # Ready to apply changes
    EXHAUSTED = "exhausted"          # No more objects to process
    BROKEN = "broken"                # Error occurred, cannot continue


@dataclass
class ProcessorSummary:
    total_objects: int
    steps_completed: int
    state: ProcessorState

    change_reports: Dict[BaseKey, ChangeReport]
    read_calls: Dict[BaseKey, List[VirtualCall]]
    write_calls: Dict[BaseKey, List[VirtualCall]]

    @property
    def total_changes(self) -> int:
        return sum(len(reports) for reports in self.change_reports.values())

    @property
    def total_read_calls(self) -> int:
        return sum(len(calls) for calls in self.read_calls.values())

    @property
    def total_write_calls(self) -> int:
        return sum(len(calls) for calls in self.write_calls.values())


class ProcessorStateError(Exception):
    pass


class Processor:
    """
    Processes a stream of koji objects in dependency-resolved order.

    Executes the read/compare/write cycle in chunks, using koji multicalls
    for efficient batch operations. Each object in the stream is expected
    to have methods for fetching state, comparing with koji data, and
    applying changes.
    """

    def __init__(
        self,
        koji_session: ClientSession,
        stream_origin: Solver,
        chunk_size: int = 100):
        """
        Initialize the processor.

        Args:
            object_stream: Iterator of koji objects in dependency-resolved order
            chunk_size: Number of objects to process in each chunk
            koji_session: Koji session for API calls
        """

        self.koji_session: ClientSession = koji_session
        self.object_stream = iter(stream_origin)
        self.chunk_size = chunk_size

        self.current_chunk: List[Base] = []
        self.state = ProcessorState.READY_CHUNK

        self.change_reports: Dict[BaseKey, ChangeReport] = {}
        self.read_logs: Dict[BaseKey, List[VirtualCall]] = {}
        self.write_logs: Dict[BaseKey, List[VirtualCall]] = {}


    def step(self, chunk_size: Optional[int] = None) -> bool:
        """
        Execute one complete cycle: read -> compare -> apply.

        Can be safely invoked from either the READY_CHUNK or READY_READ states.
        If READY_CHUNK, the current chunk is discarded and a new one is loaded.
        If there was no chunk, state is set to EXHAUSTED and 0 is returned.
        Otherwise, state is set to READY_READ and step_read, step_compare, and
        step_apply are called in order. If any of these steps fail, the state is
        set to BROKEN and an exception is raised.

        Returns:
            count of objects processed
        """

        if chunk_size is None:
            chunk_size = self.chunk_size

        if self.state == ProcessorState.READY_CHUNK:
            if not self._load_next_chunk(chunk_size):
                self.state = ProcessorState.EXHAUSTED
                return False
            self.state = ProcessorState.READY_READ

        elif self.state == ProcessorState.EXHAUSTED:
            logger.debug("step called on an exhausted processor")
            return False

        elif self.state == ProcessorState.BROKEN:
            raise ProcessorStateError(f"Processor is in the BROKEN state: {self.state}")

        count = len(self.current_chunk)

        try:
            self.step_read()
            self.step_compare()
            self.step_apply()

        except Exception:
            self.state = ProcessorState.BROKEN
            raise

        else:
            return count


    def _load_next_chunk(self, chunk_size: int) -> bool:
        """
        Load the next chunk of objects from the stream. Discards the current
        chunk.

        Note: this method ignores states, and should only be called from
        the `step()` method.

        Returns:
            True if chunk was loaded, False if stream is exhausted
        """

        self.current_chunk = []

        for _ in range(chunk_size):
            try:
                obj = next(self.object_stream)
                self.current_chunk.append(obj)
            except StopIteration:
                break

        if not self.current_chunk:
            return False

        return True


    def step_read(self) -> None:
        """
        Fetch current state from Koji for all objects in current chunk.

        This step:
        1. Creates empty change reports for each object via obj.change_report()
        2. Calls read() on each report to fetch current koji state via multicall
        3. Stores the populated reports for use in step_compare()

        After this step, change reports contain current koji data but no changes yet.
        """

        if self.state != ProcessorState.READY_READ:
            raise ProcessorStateError(f"Processor is not in the READY state: {self.state}")

        if not self.current_chunk:
            logger.debug("No objects to read from koji")
            return
        logger.debug(f"Fetching koji state for {len(self.current_chunk)} objects")

        deferred_calls = []
        with multicall(self.koji_session, associations=self.read_logs) as mc:
            for obj in self.current_chunk:

                # let our mc know to record calls with this key associated
                mc.associate(obj.key())

                # create and load the change report for this object
                change_report = obj.change_report()
                defer = change_report.read(mc)
                if defer and callable(defer):
                    # we allow the change report to return a callable to
                    # indicate it would have follow-up queries to perform.
                    # Generally these follow a pattern of doing the initial
                    # object check, and then follup calls only if it does.
                    deferred_calls.append((obj.key(), defer))

                # store it in our change reports
                self.change_reports[obj.key()] = change_report

        if deferred_calls:
            with multicall(self.koji_session, associations=self.read_logs) as mc:
                for key, call in deferred_calls:
                    mc.associate(key)
                    call(mc)

        self.state = ProcessorState.READY_COMPARE


    def step_compare(self) -> None:
        """
        Compare each object with its current koji state and identify changes.

        This step:
        1. Retrieves the change reports populated in step_read()
        2. Calls compare() on each report to analyze differences
        3. Populates the reports with specific changes that need to be made

        After this step, change reports contain both current data and required changes.
        """

        if self.state != ProcessorState.READY_COMPARE:
            raise ProcessorStateError(f"Processor is not in the READY_COMPARE state: {self.state}")

        if not self.current_chunk:
            logger.debug("No objects to compare with koji state")
            return
        logger.debug(f"Comparing {len(self.current_chunk)} objects with koji state")

        for obj in self.current_chunk:
            # get the change report for this object
            report = self.change_reports[obj.key()]

            # by now its calls from the load should have results, so we can
            # compare it with the koji state. This will cause to the report
            # to create and record any changes that need to be made.
            report.compare()

        self.state = ProcessorState.READY_APPLY


    def step_apply(self) -> None:
        """
        Apply the identified changes to the koji instance.

        This step:
        1. Retrieves the change reports with changes identified in step_compare()
        2. Calls apply() on each report to execute the changes via multicall
        3. Commits all changes to the koji instance

        After this step, the koji instance matches the desired state.
        """

        if self.state != ProcessorState.READY_APPLY:
            raise ProcessorStateError(f"Processor is not in the READY_WRITE state: {self.state}")

        if not self.current_chunk:
            logger.debug("No objects to apply changes to")
            return
        logger.debug(f"Applying changes for {len(self.current_chunk)} objects")

        with multicall(self.koji_session, associations=self.write_logs) as m:
            for obj in self.current_chunk:

                # get the change report for this object
                change_report = self.change_reports[obj.key()]

                # apply the changes to the koji instance
                change_report.apply(m)

        for obj in self.current_chunk:
            change_report = self.change_reports[obj.key()]
            change_report.check_results()

        self.state = ProcessorState.READY_CHUNK


    def run(self, step_callback: Optional[Callable[[int, int], None]] = None) -> ProcessorSummary:
        """
        Process all objects in the stream by repeatedly calling step() until we
        are in an EXHAUSTED or BROKEN state. Returns a summary of the processing
        results.

        Returns:
            Summary of processing results including total objects processed,
            changes applied, and any errors encountered.
        """

        logger.info("Starting processor run")

        total_objects = 0
        step = 0

        for step, handled in enumerate(iter(self.step, 0), 1):
            total_objects += handled
            logger.debug(f"Step #{step} processed chunk of {handled} objects")

            if step_callback:
                step_callback(step, handled)

        return ProcessorSummary(
            total_objects=total_objects,
            steps_completed=step,

            state=self.state,

            change_reports=self.change_reports,
            read_calls=self.read_logs,
            write_calls=self.write_logs,
        )


    def is_exhausted(self) -> bool:
        """Check if the object stream has been fully processed."""
        return self.state == ProcessorState.EXHAUSTED


    def is_broken(self) -> bool:
        """Check if the processor is in the BROKEN state."""
        return self.state == ProcessorState.BROKEN


class DiffOnlyProcessor(Processor):
    """
    Processor variant that only performs read and compare operations.

    Useful for the 'diff' command to show what changes would be made
    without actually applying them to the koji instance.
    """

    def step_apply(self) -> None:
        """
        Override to skip write operations in diff mode.

        Logs what changes would be applied instead of actually applying them.
        """

        if self.state != ProcessorState.READY_APPLY:
            raise ProcessorStateError(f"Processor is not in the READY_APPLY state: {self.state}")

        logger.info(f"DIFF MODE: Would apply changes for {len(self.change_reports)} objects")

        self.state = ProcessorState.READY_CHUNK


# The end.

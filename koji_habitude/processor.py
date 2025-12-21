"""
koji_habitude.processor

Core processing engine for synchronizing koji objects with a hub instance.
Handles the read/compare/write cycle in chunks with multicall optimization.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Assisted, Mostly Human


import logging
from dataclasses import dataclass
from enum import Enum
from itertools import chain, islice
from typing import Callable, Dict, Iterable, Iterator, List, Optional
from typing_extensions import TypeAlias

from koji import ClientSession, VirtualCall

from .koji import multicall
from .models.base import BaseKey, BaseObject
from .models.change import ChangeReport
from .resolver import Resolver

logger = logging.getLogger(__name__)


class ProcessorStateError(Exception):
    pass


StepCallback: TypeAlias = Callable[[int, int], None]


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

    @property
    def total_changes(self) -> int:
        return sum(len(reports) for reports in self.change_reports.values())


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
            dataseries: Iterable[BaseObject],
            resolver: Resolver,
            chunk_size: int = 100,
            skip_phantoms: bool = False,
            spinner_fn: Callable[[str], None] = None):
        """
        Initialize the processor.

        :param koji_session: Koji session for API calls
        :param dataseries: Iterator of koji objects in dependency-resolved
          order
        :param resolver: Resolver for dependency resolution
        :param chunk_size: Number of objects to process in each chunk
        :param skip_phantoms: Whether to skip phantoms
        :param spinner_fn: Function to call with a spinner message
        """

        self.koji_session: ClientSession = koji_session
        self.dataseries: Iterator[BaseObject] = iter(dataseries)
        self.resolver: Resolver = resolver
        self.chunk_size: int = chunk_size
        self.skip_phantoms: bool = skip_phantoms

        self.current_chunk: List[BaseObject] = []
        self.state: ProcessorState = ProcessorState.READY_CHUNK

        self.change_reports: Dict[BaseKey, ChangeReport] = {}
        self.spinner_fn: Callable[[str], None] = spinner_fn

        self.read_batch_size: int = chunk_size
        self.apply_batch_size: int = chunk_size * 5


    def spin(self, message: str = None) -> None:
        """
        Call the spinner function with an optional message. The spinner
        function can tick over whether or not there's a new message.
        """

        if message:
            logger.debug(message)
        if self.spinner_fn:
            self.spinner_fn(message)


    def step(self, chunk_size: Optional[int] = None) -> int:
        """
        Execute one complete cycle: read -> compare -> apply.

        Can be safely invoked from either the READY_CHUNK or READY_READ
        states. If READY_CHUNK, the current chunk is discarded and a new one
        is loaded. If there was no chunk, state is set to EXHAUSTED and 0 is
        returned. Otherwise, state is set to READY_READ and step_read,
        step_compare, and step_apply are called in order. If any of these
        steps fail, the state is set to BROKEN and an exception is raised.

        :returns: count of objects processed
        """

        if chunk_size is None:
            chunk_size = self.chunk_size

        if self.state == ProcessorState.READY_CHUNK:
            self.current_chunk = list(islice(self.dataseries, chunk_size))
            if not self.current_chunk:
                self.state = ProcessorState.EXHAUSTED
                return 0

            self.state = ProcessorState.READY_READ

        elif self.state == ProcessorState.EXHAUSTED:
            logger.debug("step called on an exhausted processor")
            return 0

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


    def step_read(self) -> None:
        """
        Fetch current state from Koji for all objects in current chunk.

        This step:

         1. Creates empty change reports for each object via
            obj.change_report()

         2. Calls read() on each report to fetch current koji state via
            multicall

         3. Stores the populated reports for use in step_compare()

        After this step, change reports contain current koji data but no
        changes yet.
        """

        if self.state != ProcessorState.READY_READ:
            raise ProcessorStateError(f"Processor is not in the READY state: {self.state}")

        if not self.current_chunk:
            logger.debug("No objects to read from koji")
            return

        self.spin(f"Fetching koji state for {len(self.current_chunk)} objects")

        batch = self.read_batch_size

        deferred_calls = []
        with multicall(self.koji_session, batch=batch) as mc:
            for obj in self.current_chunk:

                # create and load the change report for this object
                change_report = obj.change_report(self.resolver)
                defer = change_report.read(mc)
                if defer and callable(defer):
                    # we allow the change report to return a callable to
                    # indicate it would have follow-up queries to perform.
                    # Generally these follow a pattern of doing the initial
                    # object check, and then follup calls only if it does.
                    deferred_calls.append(defer)

                # store it in our change reports
                self.change_reports[obj.key()] = change_report

        if deferred_calls:
            with multicall(self.koji_session, batch=batch) as mc:
                for call in deferred_calls:
                    call(mc)

        self.state = ProcessorState.READY_COMPARE


    def step_compare(self) -> None:
        """
        Compare each object with its current koji state and identify changes.

        This step:

          1. Retrieves the change reports populated in step_read()

          2. Calls compare() on each report to analyze differences

          3. Populates the reports with specific changes that need to be made

        After this step, change reports contain both current data and required
        changes.
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

          1. Retrieves the change reports with changes identified in
             step_compare()

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

        # this is horribly over-complicated because at any point in the loop
        # we may need to break out of the multicall and continue with that
        # object and the rest of the work in a new multicall. Why? Because tag
        # inheritance can ONLY be added by using the parent tag's ID, not by
        # name. So if we're adding the parent tag, we don't know its ID until
        # after that multicall has run. This one quirk of the koji API is the
        # cause of a LOT of pain and complexity.

        batch = self.apply_batch_size

        work = iter(self.current_chunk)
        holdover = next(work)

        while holdover:
            work_segment = chain([holdover], work)
            holdover = None
            work_check = []

            with multicall(self.koji_session, batch=batch) as m:
                for obj in work_segment:

                    # get the change report for this object
                    change_report = self.change_reports[obj.key()]

                    # check if the damned thing needs to break out of the
                    # multicall this should only happen for tag inheritance
                    # where the parent tag is being created in this same
                    # multicall.
                    if change_report.break_multicall():
                        holdover = obj
                        break

                    # apply the changes to the koji instance
                    change_report.apply(m, skip_phantoms=self.skip_phantoms)
                    work_check.append(obj)

            # check the results of all the changes. This will raise an exception
            # if the apply failed for some reason.
            for obj in work_check:
                change_report = self.change_reports[obj.key()]
                change_report.check_results()

        self.state = ProcessorState.READY_CHUNK


    def run(self,
            step_callback: Optional[StepCallback] = None) -> ProcessorSummary:
        """
        Process all objects in the stream by repeatedly calling step() until
        we are in an EXHAUSTED or BROKEN state. Returns a summary of the
        processing results.

        :returns: Summary of processing results including total objects
            processed, changes applied, and any errors encountered.
        """
        total_objects = 0
        step = 0

        for step, handled in enumerate(iter(self.step, 0), 1):
            total_objects += handled

            if step_callback:
                step_callback(step, handled)

        return ProcessorSummary(
            total_objects=total_objects,
            steps_completed=step,

            state=self.state,

            change_reports=self.change_reports)


    def is_exhausted(self) -> bool:
        """
        Check if the object stream has been fully processed.

        :returns: True if the processor is in the EXHAUSTED state, False
            otherwise
        """
        return self.state == ProcessorState.EXHAUSTED


    def is_broken(self) -> bool:
        """
        Check if the processor is in the BROKEN state.

        :returns: True if the processor is in the BROKEN state, False
            otherwise
        """
        return self.state == ProcessorState.BROKEN


class CompareOnlyProcessor(Processor):
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

        self.state = ProcessorState.READY_CHUNK


# The end.

"""
koji_habitude.workflow

Workflow class for orchestrating the synchronization process.

The steps and imports required for working with habitude are long and involved,
so this class provides a simple interface for orchestrating the workflow,
allowing for users to focus on the data and configuration, rather than the
implementation details. The interface is designed to be extensible, allowing for
users to override the default behavior for each step of the workflow. The
workflow process is also designed to be pauseable, allowing for users to pause
the workflow and resume it later.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: Pure Human


from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterator, List, Type

from .koji import ClientSession, session
from .loader import MultiLoader, YAMLLoader
from .models import Base
from .namespace import Namespace, TemplateNamespace
from .processor import DiffOnlyProcessor, Processor, ProcessorSummary
from .resolver import Resolver, Report
from .solver import Solver


class WorkflowState(Enum):
    """
    The states of the workflow.

    See the `Workflow.run` and `Workflow.resume` methods for more information.

    These values are passed to the callback `Workflow.workflow_state_change`
    when the workflow transitions between states. The callback can return True
    to pause the workflow, in which case `Workflow.resume` can be called to
    resume the workflow from the current state.
    """

    READY = "ready"
    STARTING = "starting"
    LOADING = "loading"
    LOADED = "loaded"
    SOLVING = "solving"
    SOLVED = "solved"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    PROCESSING = "processing"
    PROCESSED = "processed"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowStateError(Exception):
    """
    Exception raised when the workflow is in an invalid state.
    """
    pass


class WorkflowMissingObjectsError(Exception):
    """
    Exception raised when the workflow has missing objects.
    """
    def __init__(self, message: str, report: Report):
        super().__init__(message)
        self.report = report


@dataclass
class Workflow:

    paths: List[str | Path] = None
    template_paths: List[str | Path] = None
    profile: str = 'koji'
    chunk_size: int = 100

    cls_multiloader: Type[MultiLoader] = MultiLoader
    cls_yamlloader: Type[YAMLLoader] = YAMLLoader
    cls_template_namespace: Type[TemplateNamespace] = TemplateNamespace
    cls_namespace: Type[Namespace] = Namespace
    cls_processor: Type[Processor] = Processor
    cls_resolver: Type[Resolver] = Resolver
    cls_solver: Type[Solver] = Solver

    namespace: Namespace = field(init=False, default=None)
    processor: Processor = field(init=False, default=None)
    resolver: Resolver = field(init=False, default=None)
    solver: Solver = field(init=False, default=None)
    session: ClientSession = field(init=False, default=None)

    dataseries: List[Base] = field(init=False, default=None)
    summary: ProcessorSummary = field(init=False, default=None)
    missing_report: Report = field(init=False, default=None)

    state: WorkflowState = field(init=False, default=WorkflowState.READY)
    _iter_workflow: Iterator[bool] = field(init=False, default=None)


    def load_yaml(self, paths: List[str | Path]) -> Iterator[Dict[str, Any]]:
        ml = self.cls_multiloader([self.cls_yamlloader])
        return ml.load(paths)


    def load_templates(self, paths: List[str | Path]) -> TemplateNamespace:
        template_ns = self.cls_template_namespace()
        template_ns.feedall_raw(self.load_yaml(paths))
        template_ns.expand()
        return template_ns


    def load_data(self, paths: List[str | Path], templates: TemplateNamespace = None) -> Namespace:
        data_ns = self.cls_namespace()
        if templates:
            data_ns._templates.update(templates._templates)
        data_ns.feedall_raw(self.load_yaml(paths))
        data_ns.expand()
        return data_ns


    def get_session(self, profile: str = 'koji') -> ClientSession:
        return session(profile, authenticate=True)


    def state_change(self, from_state: WorkflowState, to_state: WorkflowState):
        if self.state != from_state:
            raise WorkflowStateError(f"Workflow state ({from_state}) not as expected: {self.state}")
        self.state = to_state
        return self.workflow_state_change(from_state, to_state)


    def run_loading(self):
        yield self.state_change(WorkflowState.STARTING, WorkflowState.LOADING)
        if self.template_paths:
            self.namespace = self.load_data(self.paths, templates=self.load_templates(self.template_paths))
        else:
            self.namespace = self.load_data(self.paths)
        yield self.state_change(WorkflowState.LOADING, WorkflowState.LOADED)


    def run_solving(self):
        yield self.state_change(WorkflowState.LOADED, WorkflowState.SOLVING)
        self.resolver = self.cls_resolver(self.namespace)
        self.solver = self.cls_solver(self.resolver)
        self.solver.prepare()
        self.dataseries = list(self.solver)
        yield self.state_change(WorkflowState.SOLVING, WorkflowState.SOLVED)


    def run_connecting(self):
        yield self.state_change(WorkflowState.SOLVED, WorkflowState.CONNECTING)
        self.session = self.get_session(self.profile)
        yield self.state_change(WorkflowState.CONNECTING, WorkflowState.CONNECTED)


    def review_missing_report(self):
        """
        Review the missing report and raise an exception if there are any missing objects.
        """
        if len(self.missing_report.missing) > 0:
            self.state = WorkflowState.FAILED
            raise WorkflowMissingObjectsError(
                f"Missing {len(self.missing_report.missing)} objects",
                self.missing_report)


    def run_processing(self):
        yield self.state_change(WorkflowState.CONNECTED, WorkflowState.PROCESSING)

        missing_report = self.resolver.report()
        if missing_report.missing:
            missing_processor = DiffOnlyProcessor(
                koji_session=self.session,
                stream_origin=missing_report.missing.values(),
                resolver=self.resolver,
                chunk_size=self.chunk_size
            )
            missing_processor.run()
            missing_report = missing_processor.report()

        self.missing_report = missing_report
        self.review_missing_report()

        self.processor = self.cls_processor(
            koji_session=self.session,
            stream_origin=self.dataseries,
            resolver=self.resolver,
            chunk_size=self.chunk_size
        )
        self.summary = self.processor.run(self.processor_step_callback)
        yield self.state_change(WorkflowState.PROCESSING, WorkflowState.PROCESSED)


    def iter_run(self):
        yield self.state_change(WorkflowState.READY, WorkflowState.STARTING)
        yield from self.run_loading()
        yield from self.run_solving()
        yield from self.run_connecting()
        yield from self.run_processing()
        yield self.state_change(WorkflowState.PROCESSED, WorkflowState.COMPLETED)


    def run(self):
        """
        Run the workflow, starting from the READY state and iterating over the
        phases. As the workflow progresses, state transitions are triggered, and
        the overridable callback `workflow_state_change` is invoked. If the
        callback returns True, the workflow is paused and this method returns
        True. If the workflow completes successfully, this method returns False.

        A paused workflow can be resumed by calling the `resume` method, which
        will pick up where the workflow left off, and may be paused again.
        """

        if self.state != WorkflowState.READY:
            raise WorkflowStateError(f"Workflow state ({self.state}) not as expected: {WorkflowState.READY}")

        try:
            self._iter_workflow = self.iter_run()
            for phase_result in self._iter_workflow:
                if phase_result is True:
                    self.workflow_paused()
                    return True

        except Exception as e:
            self._iter_workflow = None
            self.state = WorkflowState.FAILED
            raise

        else:
            self._iter_workflow = None
            return False


    def resume(self):
        """
        Resume a paused workflow, starting from the current state and iterating
        over the phases. As the workflow progresses, state transitions are
        triggered, and the overridable callback `workflow_state_change` is
        invoked. If the callback returns True, the workflow is paused and this
        method returns True. If the workflow completes successfully, this method
        returns False.
        """

        if self.state in (WorkflowState.READY, WorkflowState.COMPLETED, WorkflowState.FAILED):
            raise WorkflowStateError(f"Cannot resume workflow from state: {self.state}")

        if self._iter_workflow is None:
            raise WorkflowStateError(f"Workflow is missing its internal iterator, despite the state: {self.state}")

        try:
            for phase_result in self._iter_workflow:
                if phase_result is True:
                    self.workflow_paused()
                    return True

        except Exception as e:
            self._iter_workflow = None
            self.state = WorkflowState.FAILED
            raise

        else:
            self._iter_workflow = None
            return False


    def workflow_state_change(self, from_state: WorkflowState, to_state: WorkflowState) -> bool:
        """
        Callback for the workflow, invoked during the phases of the `Workflow.run()` invocation.
        """
        return False


    def workflow_paused(self):
        """
        Callback for the workflow, invoked when the workflow is paused.
        """
        pass


    def processor_step_callback(self, step: int, handled: int):
        """
        Callback for the processor, invoked after each `processor.step()` invocation.
        """
        pass


class SyncWorkflow(Workflow):
    def __init__(
        self,
        paths: List[str | Path],
        template_paths: List[str | Path] = None,
        profile: str = 'koji',
        chunk_size: int = 100):

        super().__init__(paths, template_paths, profile, chunk_size)


class DiffWorkflow(Workflow):

    def __init__(
        self,
        paths: List[str | Path],
        template_paths: List[str | Path] = None,
        profile: str = 'koji',
        chunk_size: int = 100):

        super().__init__(
            paths, template_paths, profile, chunk_size,
            cls_processor=DiffOnlyProcessor)


    def review_missing_report(self):
        """
        Diff mode is allowed to have missing objects, so we don't need to do anything.
        """
        pass


    def get_session(self, profile: str = 'koji') -> ClientSession:
        """
        Override the default session creation to not authenticate.
        """
        return session(profile, authenticate=False)


# The end.

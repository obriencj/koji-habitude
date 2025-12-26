"""
koji_habitude.workflow

Workflow class for orchestrating the synchronization process.

The steps and imports required for working with habitude are long and
involved, so this class provides a simple interface for orchestrating
the workflow, allowing for users to focus on the data and
configuration, rather than the implementation details. The interface
is designed to be extensible, allowing for users to override the
default behavior for each step of the workflow. The workflow process
is also designed to be pauseable, allowing for users to pause the
workflow and resume it later.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: Pure Human


from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterator, List, Type, Union

from .koji import ClientSession, session
from .loader import MultiLoader, YAMLLoader
from .models import BaseObject
from .namespace import Namespace, TemplateNamespace, Redefine
from .processor import CompareOnlyProcessor, Processor, ProcessorSummary
from .resolver import Resolver, ResolverReport
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
    RESOLVING = "resolving"
    RESOLVED = "resolved"
    PROCESSING = "processing"
    PROCESSED = "processed"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowStateError(Exception):
    """
    Exception raised when the workflow is in an invalid state.
    """
    pass


class WorkflowPhantomsError(Exception):
    """
    Exception raised when the workflow has phantoms.
    """
    def __init__(self, message: str, report: ResolverReport):
        super().__init__(message)
        self.report = report


@dataclass
class Workflow:
    """
    A Workflow represents the combination of the individual features and steps
    of koji-habitude, providing a simplified interface for loading YAML,
    feeding and validating the data into a Namespace, expanding templates,
    resolving dependencies, identifying change sets, and applying the relevant
    changes onto a Koji hub instance.
    """

    paths: List[Union[str, Path]] = None
    template_paths: List[Union[str, Path]] = None
    recursive: bool = False
    profile: str = 'koji'
    chunk_size: int = 100
    skip_phantoms: bool = False

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

    dataseries: List[BaseObject] = field(init=False, default=None)
    summary: ProcessorSummary = field(init=False, default=None)
    resolver_report: ResolverReport = field(init=False, default=None)

    state: WorkflowState = field(init=False, default=WorkflowState.READY)
    _iter_workflow: Iterator[bool] = field(init=False, default=None)


    def load_yaml(self, paths: List[Union[str, Path]]) -> Iterator[Dict[str, Any]]:
        ml = self.cls_multiloader([self.cls_yamlloader])
        return ml.load(paths, recursive=self.recursive)


    def load_templates(self, paths: List[Union[str, Path]]) -> TemplateNamespace:
        template_ns = self.cls_template_namespace()
        template_ns.feedall_raw(self.load_yaml(paths))
        template_ns.expand()
        return template_ns


    def load_data(
            self,
            paths: List[Union[str, Path]],
            templates: TemplateNamespace = None) -> Namespace:

        data_ns = self.cls_namespace()
        if templates:
            data_ns.merge_templates(templates, redefine=Redefine.ALLOW)
        data_ns.feedall_raw(self.load_yaml(paths))
        data_ns.expand()
        return data_ns


    def get_session(self, profile: str = 'koji') -> ClientSession:
        return session(profile, authenticate=True)


    def state_change(
            self,
            from_state: WorkflowState,
            to_state: WorkflowState):

        if self.state != from_state:
            msg = (f"Workflow state ({from_state})"
                   f" not as expected: {self.state}")
            raise WorkflowStateError(msg)

        self.state = to_state
        return self.workflow_state_change(from_state, to_state)


    def run_loading(self):
        yield self.state_change(WorkflowState.STARTING,
                                WorkflowState.LOADING)
        if self.template_paths:
            self.namespace = self.load_data(
                self.paths,
                templates=self.load_templates(self.template_paths))
        else:
            self.namespace = self.load_data(self.paths)
        yield self.state_change(WorkflowState.LOADING,
                                WorkflowState.LOADED)


    def run_solving(self):
        yield self.state_change(WorkflowState.LOADED,
                                WorkflowState.SOLVING)
        self.resolver = self.cls_resolver(self.namespace)
        self.solver = self.cls_solver(self.resolver)
        self.solver.prepare()
        self.dataseries = list(self.solver)
        yield self.state_change(WorkflowState.SOLVING,
                                WorkflowState.SOLVED)


    def run_connecting(self):
        yield self.state_change(WorkflowState.SOLVED,
                                WorkflowState.CONNECTING)
        self.session = self.get_session(self.profile)
        yield self.state_change(WorkflowState.CONNECTING,
                                WorkflowState.CONNECTED)


    def run_resolving(self):
        yield self.state_change(WorkflowState.CONNECTED,
                                WorkflowState.RESOLVING)

        self.resolver.load_remote_references(self.session)
        self.resolver_report = self.resolver.report()
        self.review_resolver_report()

        yield self.state_change(WorkflowState.RESOLVING,
                                WorkflowState.RESOLVED)


    def review_resolver_report(self):
        """
        Review the resolver report and raise an exception if there
        are any phantoms.
        """

        phantoms = self.resolver_report.phantoms
        if len(phantoms) > 0 and not self.skip_phantoms:
            self.state = WorkflowState.FAILED
            raise WorkflowPhantomsError(
                f"Phantoms objects: {len(phantoms)}",
                self.resolver_report)


    def run_processing(self):
        yield self.state_change(WorkflowState.RESOLVED,
                                WorkflowState.PROCESSING)

        self.processor = self.cls_processor(
            koji_session=self.session,
            dataseries=self.dataseries,
            resolver=self.resolver,
            chunk_size=self.chunk_size,
            skip_phantoms=self.skip_phantoms
        )
        self.summary = self.processor.run(self.processor_step_callback)
        yield self.state_change(WorkflowState.PROCESSING,
                                WorkflowState.PROCESSED)


    def iter_run(self):
        yield self.state_change(WorkflowState.READY,
                                WorkflowState.STARTING)
        yield from self.run_loading()
        yield from self.run_solving()
        yield from self.run_connecting()
        yield from self.run_resolving()
        yield from self.run_processing()
        yield self.state_change(WorkflowState.PROCESSED,
                                WorkflowState.COMPLETED)


    def run(self) -> WorkflowState:
        """
        Run the workflow, starting from the READY state and iterating over the
        phases. As the workflow progresses, state transitions are triggered,
        and the overridable callback `workflow_state_change` is invoked. If
        the callback returns True, the workflow is paused and this method
        returns the current state. If the workflow completes successfully,
        this method returns `WorkflowState.COMPLETED`.

        A paused workflow can be resumed by calling the `resume` method, which
        will pick up where the workflow left off, and may be paused again.

        If an exception is raised during the run, the workflow state is set to
        `WorkflowState.FAILED` and the exception is re-raised.
        """

        if self.state != WorkflowState.READY:
            msg = (f"Workflow state ({self.state})"
                   f" not as expected: {WorkflowState.READY}")
            raise WorkflowStateError(msg)

        try:
            self._iter_workflow = self.iter_run()
            for phase_result in self._iter_workflow:
                if phase_result is True:
                    self.workflow_paused()
                    return self.state

        except Exception:
            self._iter_workflow = None
            self.state = WorkflowState.FAILED
            raise

        else:
            self._iter_workflow = None
            return self.state


    def resume(self):
        """
        Resume a paused workflow, starting from the current state
        and iterating over the phases. As the workflow progresses,
        state transitions are triggered, and the overridable callback
        `workflow_state_change` is invoked. If the callback returns
        True, the workflow is paused and this method returns True. If
        the workflow completes successfully, this method returns
        False.
        """

        if self.state in (WorkflowState.READY, WorkflowState.COMPLETED,
                          WorkflowState.FAILED):
            msg = f"Cannot resume workflow from state: {self.state}"
            raise WorkflowStateError(msg)

        if self._iter_workflow is None:
            msg = (f"Workflow is missing its internal iterator,"
                   f" despite the state: {self.state}")
            raise WorkflowStateError(msg)

        try:
            for phase_result in self._iter_workflow:
                if phase_result is True:
                    self.workflow_paused()
                    return True

        except Exception:
            self._iter_workflow = None
            self.state = WorkflowState.FAILED
            raise

        else:
            self._iter_workflow = None
            return False


    def workflow_state_change(
            self,
            from_state: WorkflowState,
            to_state: WorkflowState) -> bool:
        """
        Callback for the workflow, invoked during the phases of
        the `Workflow.run()` invocation.
        """

        return False


    def workflow_paused(self):
        """
        Callback for the workflow, invoked when the workflow is paused.
        """

        pass


    def processor_step_callback(self, step: int, handled: int):
        """
        Callback for the processor, invoked after each `processor.step()`
        invocation.
        """

        pass


class ApplyWorkflow(Workflow):
    """
    Workflow for applying data onto a Koji hub instance. Implements the majority
    of the behavior of the `apply` command.
    """

    def __init__(
            self,
            paths: List[Union[str, Path]],
            template_paths: List[Union[str, Path]] = None,
            recursive: bool = False,
            profile: str = 'koji',
            chunk_size: int = 100,
            skip_phantoms: bool = False):

        super().__init__(
            paths=paths,
            template_paths=template_paths,
            recursive=recursive,
            profile=profile,
            chunk_size=chunk_size,
            skip_phantoms=skip_phantoms)


class CompareWorkflow(Workflow):
    """
    Workflow for comparing data against a Koji hub instance. Implements the
    majority of the behavior of the `compare` command. Similar to the
    `ApplyWorkflow` in most aspects, but with a processor that omits the apply
    operations.
    """

    def __init__(
            self,
            paths: List[Union[str, Path]],
            template_paths: List[Union[str, Path]] = None,
            recursive: bool = False,
            profile: str = 'koji',
            chunk_size: int = 100,
            skip_phantoms: bool = False):

        super().__init__(
            paths=paths,
            template_paths=template_paths,
            recursive=recursive,
            profile=profile,
            chunk_size=chunk_size,
            skip_phantoms=skip_phantoms,
            cls_processor=CompareOnlyProcessor)


    def review_resolver_report(self):
        """
        Diff mode is allowed to have phantoms, so we don't need to do anything.
        """

        pass


    def get_session(self, profile: str = 'koji') -> ClientSession:
        """
        Override the default session creation to not authenticate.
        """

        return session(profile, authenticate=False)


@dataclass
class DictWorkflow(Workflow):
    """
    Workflow for operating over pre-created dictionaries of objects, rather
    than using a loader to pull data from a filesystem.
    """

    objects: List[Dict[str, Any]] = field(default_factory=list)

    def load_data(
            self,
            paths: List[Union[str, Path]],
            templates: TemplateNamespace = None) -> Namespace:

        data_ns = self.cls_namespace()
        if templates:
            data_ns.merge_templates(templates)
        data_ns.feedall_raw(self.objects)
        data_ns.expand()
        return data_ns


class ApplyDictWorkflow(DictWorkflow):
    """
    Workflow for applying data onto a Koji hub instance, using pre-created
    dictionaries of objects.

    This is used by the `template apply` command to apply a single template's
    expansion onto a Koji hub instance.
    """

    def __init__(
            self,
            objects: List[Dict[str, Any]],
            template_paths: List[Union[str, Path]] = None,
            profile: str = 'koji',
            chunk_size: int = 100,
            skip_phantoms: bool = False):
        super().__init__(
            objects=objects,
            template_paths=template_paths,
            profile=profile,
            chunk_size=chunk_size,
            skip_phantoms=skip_phantoms)


class CompareDictWorkflow(DictWorkflow):
    """
    Workflow for comparing data against a Koji hub instance, using pre-created
    dictionaries of objects.

    This is used by the `template compare` command to compare a single
    template's expansion against the objects on a Koji hub instance.
    """

    def __init__(
            self,
            objects: List[Dict[str, Any]],
            template_paths: List[Union[str, Path]] = None,
            profile: str = 'koji',
            chunk_size: int = 100,
            skip_phantoms: bool = False):
        super().__init__(
            objects=objects,
            template_paths=template_paths,
            profile=profile,
            chunk_size=chunk_size,
            skip_phantoms=skip_phantoms,
            cls_processor=CompareOnlyProcessor)


    def review_resolver_report(self):
        """
        Diff mode is allowed to have phantoms, so we don't need to do anything.
        """

        pass


    def get_session(self, profile: str = 'koji') -> ClientSession:
        """
        Override the default session creation to not authenticate.
        """

        return session(profile, authenticate=False)


# The end.

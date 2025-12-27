"""
koji-habitude - models.change

Base classes for Change and ChangeReport

Each model needs to be able to provide subclasses of these in order to fully
represent their changes when comparing to the data in a koji instance.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Assisted, Mostly Human


from dataclasses import dataclass, field
from enum import Enum
from logging import getLogger
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Iterable, List,
                    Optional)

from koji import GenericError, MultiCallSession, VirtualCall

from ..exceptions import ChangeApplyError, ChangeReadError
from .base import BaseObject, BaseKey

if TYPE_CHECKING:
    from ..resolver import Resolver
    from .base import ResolvableMixin as Resolvable


logger = getLogger(__name__)


class ChangeError(Exception):
    pass


class ChangeReportError(Exception):
    pass


class ChangeState(Enum):
    """
    States of a Change's lifecycle
    """

    PENDING = 'Pending'
    APPLIED = 'Applied'
    SKIPPED = 'Skipped'
    FAILED = 'Failed'


class ChangeReportState(Enum):
    """
    States of a ChangeReport's lifecycle
    """

    PENDING = 'Pending'
    LOADING = 'Loading'
    LOADED = 'Loaded'
    COMPARING = 'Comparing'
    COMPARED = 'Compared'
    APPLYING = 'Applying'
    APPLIED = 'Applied'
    CHECKING = 'Checking'
    CHECKED = 'Checked'
    ERROR = 'Error'


@dataclass
class Change:
    """
    Represents an atomic change in Koji, applicable to a single Base object.
    """

    obj: BaseObject

    _skippable: ClassVar[bool] = False

    _result: Optional[VirtualCall] = field(default=None, init=False)
    _state: ChangeState = field(default=ChangeState.PENDING, init=False)


    @property
    def state(self) -> ChangeState:
        return self._state


    def apply(self, session: MultiCallSession) -> None:
        """
        Apply a change to the Koji instance. This will call the `impl_apply`
        method to perform the actual work, which will need to be overridden by
        subclasses.

        Records the result of the change call, which can be accessed via the
        `result` method.

        :param session: The Koji multicall session
        :raises ChangeError: If the change has already been applied
        """

        if self._state == ChangeState.SKIPPED:
            logger.debug(f"Skipping apply of change: {self!r}")
            return
        if self._state != ChangeState.PENDING:
            raise ChangeError(f"Attempted to re-apply change: {self!r}")
        logger.debug(f"Applying change: {self!r}")
        self._result = self.impl_apply(session)
        self._state = ChangeState.APPLIED


    def impl_apply(self, session: MultiCallSession) -> VirtualCall:
        """
        This method is called by the `apply` method to perform the actual work,
        and should not be called directly.

        Subclasses of Change must implement this method to perform the actual
        work of applying the change to the Koji instance.

        :param session: The Koji multicall session
        :returns: The result of the change call, to be recorded by this instance via the invoking `apply` method
        """

        raise NotImplementedError("Subclasses of Change must implement impl_apply")


    def skip_check(self, resolver: 'Resolver') -> bool:
        """
        Returns True if the change is skippable, and needs skipping, False
        otherwise. This is used in situations where the change depends on a
        phantom object (ie. is a Reference, and does not exist on the Koji instance)

        :param resolver: The resolver instance
        :returns: True if the change should be skipped, False otherwise
        """

        if self._skippable:
            return self.skip_check_impl(resolver)
        return False


    def skip_check_impl(self, resolver: 'Resolver') -> bool:
        """
        This method is called by the `skip_check` method to perform the skip determination,
        and should not be called directly.

        :param resolver: The resolver instance
        :returns: True if the change should be skipped, False otherwise
        """
        raise NotImplementedError("Skippable Subclasses of Change must implement skip_impl")


    def result(self) -> Any:
        """
        The result of the change call, as returned by the Koji session. If the
        change has not been applied, this will raise a ChangeError. If the call
        failed, this will raise the underlying exception returned by the Koji
        instance.

        Note that this method is what allows a Change to determine whether it
        has failed or not. It's possible that going into this, the state will be
        APPLIED, but if the call fails, the state will be FAILED.

        :returns: The result of the change call
        :raises ChangeError: If the change has not been applied
        """

        if self._state == ChangeState.SKIPPED:
            return None
        if self._state == ChangeState.PENDING:
            raise ChangeError(f"Change not applied: {self!r}")

        try:
            return self._result.result
        except Exception:
            self._state = ChangeState.FAILED
            raise


    def skip(self) -> None:
        """
        Mark the change as skipped. This will prevent the apply method from being
        called, and will cause the result method to return None.

        :raises ChangeError: If the change is not in PENDING state
        """

        # note, we don't call the skip_check or skip_check_impl again. If
        # someone says we should skip it, well then we should skip it. Ideally
        # they will only do so after they've checked first, but maybe there will
        # be other reasons, too.

        if self._state != ChangeState.PENDING:
            raise ChangeError(f"Attempted to skip change: {self!r}")

        logger.debug(f"Skipping change: {self!r}")
        self._state = ChangeState.SKIPPED


    def explain(self) -> str:
        """
        Return a human-readable explanation of what this change will do.

        Subclasses should override this method to provide specific explanations.

        :returns: Human-readable explanation of the change
        """

        return f"Apply {self.__class__.__name__} for {self.obj.typename} {self.obj.name}"


    def break_multicall(self, resolver: 'Resolver') -> bool:
        """
        A special edge-case method to allows a change to break out of a
        multicall and be given its own fresh multicall. This is only used by the
        TagAddInheritance change, which needs to lookup and parent tag IDs in
        order to make its call. Those parents may not exist yet, if they are
        being added in the same multicall, and so that single change is
        permitted to return True from this method in order to let its parents
        first be created.

        If the Koji API ever allows for the `setInheritanceData` call to operate
        on parent tags by name rather than by ID, then this method can be
        removed and the process for applying changes can be greatly simplified.

        :param resolver: The resolver instance
        :returns: True if this change should break out of the current multicall
        """

        return False


    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(state={self.state})>"


    def __str__(self) -> str:
        return self.explain()


@dataclass
class Create(Change):
    """
    Creates a new object in Koji.

    Subclasses should implement summary() to provide a description of what's
    being created (without the "Create" verb). The explain() method will
    automatically prepend "Create" to the summary.

    For complex cases, subclasses can override explain() directly.

    Example summary(): "tag 'f39-build' with arches [x86_64, aarch64]"
    Example explain(): "Create tag 'f39-build' with arches [x86_64, aarch64]"
    """

    style_name: ClassVar[str] = 'create'

    def summary(self) -> str:
        """
        Return a minimal description of what's being created (without "Create" verb).

        Override this method to provide a summary, or override explain() directly
        for complex formatting needs.

        :returns: Minimal description without the "Create" verb
        """

        return f"Create {self.obj.typename} {self.obj.name}"


    def explain(self) -> str:
        """
        Return a full explanation of what this change will do.

        By default, this prepends "Create" to the summary(). Override this method
        directly for complex cases where the two-stage approach doesn't fit.

        :returns: Full explanation of the change
        """

        return self.summary()


@dataclass
class Update(Change):
    """
    Updates properties of an existing object.

    Subclasses should implement summary() to provide the update action with verb
    (e.g., "Lock tag", "Set permission to 'admin'"). The explain() method will
    automatically add the object context.

    For complex cases, subclasses can override explain() directly.

    Example summary(): "Lock"
    Example explain(): "Lock tag 'f39-build'"
    """

    style_name: ClassVar[str] = 'update'

    def summary(self) -> str:
        """
        Return a minimal action summary with verb.

        Override this method to provide a summary, or override explain() directly
        for complex formatting needs.
        """

        return None


    def explain(self) -> str:
        """
        Return a full explanation of what this change will do.

        By default, this adds object context to the summary(). Override this method
        directly for complex cases where the two-stage approach doesn't fit.

        :returns: Full explanation of the change
        """

        summary = self.summary()
        if summary is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} must implement summary() or explain()")

        obj_type = self.obj.typename
        # If summary ends with the object type, append the name
        if summary.endswith(obj_type):
            return f"{summary} '{self.obj.name}'"
        else:
            # Summary has specific action, add context with "for"
            return f"{summary} for {obj_type} '{self.obj.name}'"


@dataclass
class Add(Change):
    """
    Adds a feature or relation to an existing object.

    Subclasses should implement summary() to provide the addition action with verb
    (e.g., "Add package 'httpd'", "Add inheritance from 'parent'"). The explain()
    method will automatically add "to {object}" context.

    For complex cases, subclasses can override explain() directly.

    Example summary(): "Add package 'httpd'"
    Example explain(): "Add package 'httpd' to tag 'f39-build'"
    """

    style_name: ClassVar[str] = 'add'

    def summary(self) -> str:
        """
        Return a minimal action summary with "Add" verb.

        Override this method to provide a summary, or override explain() directly
        for complex formatting needs.
        """

        return None


    def explain(self) -> str:
        """
        Return a full explanation of what this change will do.

        By default, this adds "to {object}" context to the summary(). Override this
        method directly for complex cases where the two-stage approach doesn't fit.
        """

        summary = self.summary()
        if summary is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} must implement summary() or explain()")

        return f"{summary} to {self.obj.typename} {self.obj.name}"


@dataclass
class Remove(Change):
    """
    Removes a feature or relation from an existing object.

    Subclasses should implement summary() to provide the removal action with verb
    (e.g., "Remove package 'httpd'", "Remove group 'build'"). The explain()
    method will automatically add "from {object}" context.

    For complex cases, subclasses can override explain() directly.

    Example summary(): "Remove package 'httpd'"
    Example explain(): "Remove package 'httpd' from tag 'f39-build'"
    """

    style_name: ClassVar[str] = 'remove'

    def summary(self) -> str:
        """
        Return a minimal action summary with "Remove" verb.

        Override this method to provide a summary, or override explain() directly
        for complex formatting needs.
        """

        return None


    def explain(self) -> str:
        """
        Return a full explanation of what this change will do.

        By default, this adds "from {object}" context to the summary(). Override this
        method directly for complex cases where the two-stage approach doesn't fit.
        """

        summary = self.summary()
        if summary is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} must implement summary() or explain()")

        return f"{summary} from {self.obj.typename} '{self.obj.name}'"


@dataclass
class Modify(Change):
    """
    Modifies an existing feature or relation of an object.

    Subclasses should implement summary() to provide the modification action with verb
    (e.g., "Set package 'httpd' owner to 'webteam'", "Update group 'build' description").
    The explain() method will automatically add "in {object}" context.

    For complex cases, subclasses can override explain() directly.

    Example summary(): "Set package 'httpd' owner to 'webteam'"
    Example explain(): "Set package 'httpd' owner to 'webteam' in tag 'f39-build'"
    """

    style_name: ClassVar[str] = 'modify'

    def summary(self) -> str:
        """
        Return a minimal action summary with verb.

        Override this method to provide a summary, or override explain() directly
        for complex formatting needs.
        """

        return None


    def explain(self) -> str:
        """
        Return a full explanation of what this change will do.

        By default, this adds "in {object}" context to the summary(). Override this
        method directly for complex cases where the two-stage approach doesn't fit.
        """

        summary = self.summary()
        if summary is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} must implement summary() or explain()")

        return f"{summary} in {self.obj.typename} '{self.obj.name}'"


class ChangeReport:
    """
    Represents a collection of changes applicable to a single Base object. A
    ChangeReport begins empty, and proceeds through the following phases in
    order to collect changes:

    * a Processor instance will create the ChangeReport instance from the
      initial Base object

    * state is PENDING

    * `read` is called by the Processor with a multicall session, allowing the
      report to invoke calls against Koji.

    * state is LOADING

    * `read` in turn calls `impl_read` to perform the actual work, provided
       that it has not been called already.

    * `impl_read` must be implemented by subclasses to perform the actual
       necessary calls to fetch the current koji state.

    * `impl_read` may return None to indicate that no follow-up calls are
       needed, or it may return a callable. The callable will be invoked in a
       separate, later multicall session, allowing the object to first check
       whether it exists in the system at all before proceeding with additional
       checks that will be guaranteed to fail if the object is not found.

    * the Processor allows the multicall session to be close, which populates
      the results of all the calls made in the `impl_read` call. If there are
      followup calls, they will be invoked in a new multicall session at that
      point.

    * state is LOADED

    * `compare` is called by a Processor, allowing a subclass to compare the
      current koji state with the expected state, and identify changes.

    * state is COMPARING

    * `compare` in turn calls `impl_compare` to perform the actual work.

    * `impl_compare` must be implemented by subclasses to perform the actual
      necessary calls to compare the current koji state (as obtained during the
      `impl_read` call) with the expected state of the Base object.

    * `impl_compare` yields individual differences to be recorded as Change
      instances which are collected by the calling `compare` method.

    * state is COMPARED

    * the Processor opens a new multicall session, and invokes the `apply`
      method on the report

    * state is APPLYING

    * the report's `apply` method in turn invokes the `apply` (and indirectly
      `impl_apply`) methods of the changes in the report.

    * state is APPLIED

    * the Processor closes the multicall session, which causes each of the
      atomic changes to be applied into the Koji instance.

    * the Processor calls the `check_results` method on the report

    * state is CHECKING

    * the report's `check_results` method in turn invokes the `check_results`
      methods of the changes in the report. This gives a chance for any
      exceptions to be raised if the change calls failed.

    * state is CHECKED
    """

    def __init__(self, obj: 'Resolvable', resolver: 'Resolver'):
        self.obj: 'Resolvable' = obj
        self.key: BaseKey = obj.key()
        self.state: ChangeReportState = ChangeReportState.PENDING
        self.changes: List[Change] = []
        self.resolver: 'Resolver' = resolver


    def __len__(self):
        return len(self.changes)


    def __iter__(self):
        return iter(self.changes)


    def read(self, session: MultiCallSession) -> Optional[Callable[[MultiCallSession], None]]:
        """
        Reads the Koji state and compares it with the expected state of the Base
        object by calling the `impl_read` method.

        Requires an initial state of `PENDING`, and will progress through the
        `LOADING` and `LOADED` states.
        """

        if self.state != ChangeReportState.PENDING:
            raise ChangeReportError(f"Change report is not pending: {self.state}")

        self.state = ChangeReportState.LOADING
        defer = self.impl_read(session)

        if defer and callable(defer):
            def read_defer(session: MultiCallSession) -> None:
                if self.state != ChangeReportState.LOADING:
                    raise ChangeReportError(f"Change report is not loading: {self.state}")
                self.state = ChangeReportState.LOADED
                return defer(session)

            return read_defer
        else:
            self.state = ChangeReportState.LOADED
            return None


    def impl_read(self, session: MultiCallSession) -> Optional[Callable[[MultiCallSession], None]]:
        remote = self.obj.remote()
        if remote:
            remote.load_additional_data(session)
            return None
        else:
            self.obj.load_remote(session)
            return self.impl_read_defer


    def impl_read_defer(self, session: MultiCallSession) -> None:
        remote = self.obj.remote()
        if remote:
            remote.load_additional_data(session)


    def compare(self) -> None:
        """
        Compares the read Koji state with the expected state of the Base object
        by calling the `impl_compare` method and collectings its results.

        Requires an initial state of `LOADED`, and will progress through the
        `COMPARING` and `COMPARED` states.
        """

        if self.state != ChangeReportState.LOADED:
            raise ChangeReportError(f"Change report is not loaded: {self.state}")

        self.state = ChangeReportState.COMPARING

        try:
            self.changes.extend(self.impl_compare())
        except GenericError as e:
            # Wrap koji errors that occur when accessing VirtualCall results
            raise ChangeReadError(
                original_error=e,
                obj=self.obj,
            ) from e

        self.state = ChangeReportState.COMPARED


    def impl_compare(self) -> Iterable[Change]:
        """
        Must be implemented by subclasses to perform the actual work of
        comparing the read Koji state with the expected state of the Base
        object, yielding Change instances as they are identified.
        """

        raise NotImplementedError("Subclasses of ChangeReport must implement impl_compare")


    def apply(self, session: MultiCallSession, skip_phantoms: bool = False) -> None:
        """
        Applies the changes in the report to the Koji instance by calling the
        `apply` method on each change.

        Requires an initial state of `COMPARED`, and will progress through the
        `APPLYING` and `APPLIED` states.
        """

        if self.state != ChangeReportState.COMPARED:
            raise ChangeReportError(f"Change report is not compared: {self.state}")

        self.state = ChangeReportState.APPLYING
        logger.debug(f"Applying {len(self.changes)} changes to {self.obj.key()}")
        for change in self.changes:
            if skip_phantoms and change.skip_check(self.resolver):
                change.skip()
            else:
                change.apply(session)
        self.state = ChangeReportState.APPLIED


    def iter(
            self,
            skip_phantoms: bool = False,
            call_skip: bool = True) -> Iterable[Change]:
        """
        Iterates over the changes in the report, yielding each change.

        :param skip_phantoms: Whether to skip phantoms
        :returns: Iterable of changes
        """

        if not skip_phantoms:
            yield from self.changes
            return

        for change in self.changes:
            if change.skip_check(self.resolver):
                if call_skip:
                    change.skip()
            else:
                yield change


    def check_results(self) -> None:
        """
        Checks the results of the changes in the report. This will raise an
        exception if any change failed.

        Requires an initial state of `APPLIED`, and will progress through the
        `CHECKING` and `CHECKED` states.
        """

        if self.state != ChangeReportState.APPLIED:
            raise ChangeReportError(f"Change report is not applied: {self.state}")

        self.state = ChangeReportState.CHECKING

        for change in self.changes:
            try:
                # this will raise an exception if the change failed
                change.result()
            except GenericError as e:
                # Wrap koji errors that occur when applying changes
                # Extract method info from the VirtualCall if available
                method_name = None
                parameters = None
                if change._result:
                    method_name = getattr(change._result, '_method', None)
                    args = getattr(change._result, '_args', None)
                    kwargs = getattr(change._result, '_kwargs', None)
                    if args or kwargs:
                        parameters = {'args': args, 'kwargs': kwargs}

                raise ChangeApplyError(
                    original_error=e,
                    obj=self.obj,
                    change_description=change.explain(),
                    method_name=method_name,
                    parameters=parameters,
                ) from e

        self.state = ChangeReportState.CHECKED


    def break_multicall(self) -> bool:
        """
        Calls the `break_multicall` method on each change in the report until
        one returns True. Returns True if any change's `break_multicall` method
        returns True, else returns False.
        """

        for change in self.changes:
            if change.break_multicall(self.resolver):
                return True
        return False


# The end.

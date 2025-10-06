"""
koji-habitude - models.change

Base classes for Change and ChangeReport

Each model needs to be able to provide subclasses of these in order to fully
represent their changes when comparing to the data in a koji instance.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: Pure Human


from dataclasses import dataclass, field
from enum import Enum
from logging import getLogger
from typing import Any, Callable, ClassVar,Iterable, List, Optional, TYPE_CHECKING

from koji import MultiCallSession, VirtualCall

from .base import Base, BaseKey

if TYPE_CHECKING:
    from ..resolver import Resolver


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

        Raises a ChangeError if the change has already been applied.
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

        Returns the result of the change call, to be recorded by this instance
        via the invoking `apply` method.
        """

        raise NotImplementedError("Subclasses of Change must implement impl_apply")


    def skip_check(self, resolver: 'Resolver') -> bool:
        """
        Returns True if the change is skippable, and needs skipping, False
        otherwise. This is used in situations where the change depends on a
        phantom object (ie. is a Reference, and does not exist on the Koji instance)
        """

        if self._skippable:
            return self.skip_check_impl(resolver)
        return False


    def skip_check_impl(self, resolver: 'Resolver') -> bool:
        """
        This method is called by the `skip_check` method to perform the skip determination,
        and should not be called directly.
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
        """

        return f"Apply [{self._state.value}] {self.__class__.__name__}"


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
        """

        return False


    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(state={self.state})>"


    def __str__(self) -> str:
        return self.explain()


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

    def __init__(self, obj: Base, resolver: 'Resolver'):
        self.obj: Base = obj
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
        defer  = self.impl_read(session)

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
        """
        Must be implemented by subclasses to perform the actual work of reading
        the Koji state. This method may return None to indicate that is has
        completed its work, or a callable object that will be invoked in a
        separate, later multicall session to perform deferred lookups which will
        have the results of the initial read calls available.
        """

        raise NotImplementedError("Subclasses of ChangeReport must implement impl_read")


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
        self.changes.extend(self.impl_compare())
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
            # this will raise an exception if the change failed
            change.result()
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

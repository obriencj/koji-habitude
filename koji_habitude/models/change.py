"""
koji-habitude - models.change

Base classes for Change and ChangeReport

Each model needs to subclass these in order to fully represent their changes
when comparing to the data in a koji instance.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: Pure Human


from enum import Enum
from typing import Any, Callable, Optional, List

from koji import MultiCallSession, VirtualCall

from .base import Base, BaseKey


class ChangeError(Exception):
    pass


class ChangeReportError(Exception):
    pass


class ChangeReportState(Enum):
    PENDING = 'pending'
    LOADING = 'loading'
    LOADED = 'loaded'
    COMPARING = 'comparing'
    COMPARED = 'compared'
    APPLYING = 'applying'
    APPLIED = 'applied'
    ERROR = 'error'


class Change:

    def __init__(self) -> None:
        self._result: Optional[VirtualCall] = None

    def __post_init__(self) -> None:
        self._result = None

    def impl_apply(self, session: MultiCallSession) -> VirtualCall:
        raise NotImplementedError("Subclasses of Change must implement impl_apply")

    def apply(self, session: MultiCallSession) -> None:
        if self._result is not None:
            raise ChangeError(f"Attempted to re-apply change: {self!r}")
        self._result = self.impl_apply(session)

    @property
    def result(self) -> Any:
        if self._result is None:
            raise ChangeError(f"Change not applied: {self!r}")
        return self._result.result


class ChangeReport:

    def __init__(self, obj: Base):
        self.obj: Base = obj
        self.key: BaseKey = obj.key()
        self.state: ChangeReportState = ChangeReportState.PENDING
        self.changes: List[Change] = []


    def __len__(self):
        return len(self.changes)


    def __iter__(self):
        return iter(self.changes)


    def read(self, session: MultiCallSession) -> Callable[[MultiCallSession], None] | None:
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


    def impl_read(self, session: MultiCallSession) -> Callable[[MultiCallSession], None] | None:
        raise NotImplementedError("Subclasses of ChangeReport must implement impl_read")


    def compare(self) -> None:
        if self.state != ChangeReportState.LOADED:
            raise ChangeReportError(f"Change report is not loaded: {self.state}")
        self.state = ChangeReportState.COMPARING
        self.impl_compare()
        self.state = ChangeReportState.COMPARED


    def impl_compare(self) -> None:
        raise NotImplementedError("Subclasses of ChangeReport must implement impl_compare")


    def add(self, change: Change) -> None:
        if self.state != ChangeReportState.COMPARING:
            raise ChangeReportError(f"Change report is not comparing: {self.state}")
        self.changes.append(change)


    def apply(self, session: MultiCallSession) -> None:
        if self.state != ChangeReportState.COMPARED:
            raise ChangeReportError(f"Change report is not compared: {self.state}")

        self.state = ChangeReportState.APPLYING
        for change in self.changes:
            change.apply(session)
        self.state = ChangeReportState.APPLIED


# The end.

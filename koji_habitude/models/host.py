"""
koji-habitude - models.host

Host model for koji build host objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated with Human Rework


from dataclasses import dataclass
from typing import ClassVar, List, Sequence, Optional, Any, TYPE_CHECKING

from koji import MultiCallSession, VirtualCall, ClientSession
from pydantic import Field

from .base import BaseObject, BaseKey, BaseStatus
from .change import ChangeReport, Change

if TYPE_CHECKING:
    from ..resolver import Resolver


@dataclass
class HostCreate(Change):
    name: str
    arches: List[str]

    def impl_apply(self, session: MultiCallSession):
        return session.createHost(
            self.name,
            arches=' '.join(self.arches))

    def explain(self) -> str:
        arches_str = ', '.join(self.arches)
        return f"Create host '{self.name}' with arches [{arches_str}]"


@dataclass
class HostSetArches(Change):
    name: str
    arches: List[str]

    def impl_apply(self, session: MultiCallSession):
        return session.editHost(self.name, arches=' '.join(self.arches))

    def explain(self) -> str:
        arches_str = ', '.join(self.arches)
        return f"Set arches for host '{self.name}' to [{arches_str}]"


@dataclass
class HostSetCapacity(Change):
    name: str
    capacity: float

    def impl_apply(self, session: MultiCallSession):
        return session.editHost(self.name, capacity=self.capacity)

    def explain(self) -> str:
        return f"Set capacity for host '{self.name}' to {self.capacity}"


@dataclass
class HostSetEnabled(Change):
    name: str
    enabled: bool

    def impl_apply(self, session: MultiCallSession):
        return session.editHost(self.name, enabled=self.enabled)

    def explain(self) -> str:
        action = "Enable" if self.enabled else "Disable"
        return f"{action} host '{self.name}'"


@dataclass
class HostSetDescription(Change):
    name: str
    description: str

    def impl_apply(self, session: MultiCallSession):
        return session.editHost(self.name, description=self.description)

    def explain(self) -> str:
        return f"Set description for host '{self.name}' to '{self.description}'"


@dataclass
class HostAddChannel(Change):
    name: str
    channel: str

    _skippable: ClassVar[bool] = True

    def skip_check_impl(self, resolver: 'Resolver') -> bool:
        channel = resolver.resolve(('channel', self.channel))
        return channel.status == BaseStatus.PHANTOM

    def impl_apply(self, session: MultiCallSession):
        return session.addHostToChannel(self.name, self.channel)

    def explain(self) -> str:
        return f"Add host '{self.name}' to channel '{self.channel}'"


@dataclass
class HostRemoveChannel(Change):
    name: str
    channel: str

    def impl_apply(self, session: MultiCallSession):
        return session.removeHostFromChannel(self.name, self.channel)

    def explain(self) -> str:
        return f"Remove host '{self.name}' from channel '{self.channel}'"


class HostChangeReport(ChangeReport):

    def impl_read(self, session: MultiCallSession):
        self._hostinfo: VirtualCall = self.obj.query_exists(session)


    def impl_compare(self):
        info = self._hostinfo.result
        if not info:
            if not self.obj.was_split():
                # we don't exist, and we didn't split our create to an earlier
                # call, so create now.
                yield HostCreate(self.obj.name, self.obj.arches)

            if self.obj.capacity is not None:
                yield HostSetCapacity(self.obj.name, self.obj.capacity)
            if self.obj.enabled is not None and not self.obj.enabled:
                yield HostSetEnabled(self.obj.name, self.obj.enabled)
            if self.obj.description is not None:
                yield HostSetDescription(self.obj.name, self.obj.description)
            for channel in self.obj.channels:
                yield HostAddChannel(self.obj.name, channel)
            return

        arches = set(info['arches'].split())
        if arches != set(self.obj.arches):
            yield HostSetArches(self.obj.name, self.obj.arches)
        if self.obj.capacity is not None and info['capacity'] != self.obj.capacity:
            yield HostSetCapacity(self.obj.name, self.obj.capacity)
        if info['enabled'] != self.obj.enabled:
            yield HostSetEnabled(self.obj.name, self.obj.enabled)
        if self.obj.description is not None and info['description'] != self.obj.description:
            yield HostSetDescription(self.obj.name, self.obj.description)

        channels = info['channels']
        for channel in self.obj.channels:
            if channel not in channels:
                yield HostAddChannel(self.obj.name, channel)

        if self.obj.exact_channels:
            for channel in channels:
                if channel not in self.obj.channels:
                    yield HostRemoveChannel(self.obj.name, channel)


class Host(BaseObject):
    """
    Koji build host object model.
    """

    typename: ClassVar[str] = "host"

    arches: List[str] = Field(alias='arches', default_factory=list)
    capacity: Optional[float] = Field(alias='capacity', default=None)
    enabled: bool = Field(alias='enabled', default=True)
    description: Optional[str] = Field(alias='description', default=None)
    channels: List[str] = Field(alias='channels', default_factory=list)
    exact_channels: bool = Field(alias='exact-channels', default=False)

    _auto_split: ClassVar[bool] = True


    def split(self) -> 'Host':
        return Host(
            name=self.name,
            arches=self.arches,
            capacity=self.capacity,
            enabled=self.enabled,
            description=self.description)


    def dependency_keys(self) -> Sequence[BaseKey]:
        """
        Return dependencies for this host.
        """
        return [('channel', channel) for channel in self.channels]


    def change_report(self, resolver: 'Resolver') -> HostChangeReport:
        return HostChangeReport(self, resolver)


    @classmethod
    def check_exists(cls, session: ClientSession, key: BaseKey) -> Any:
        return session.getHost(key[1], strict=False)


# The end.

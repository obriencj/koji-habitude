"""
koji-habitude - models.host

Host model for koji build host objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""


from dataclasses import dataclass
from typing import ClassVar, List, Sequence, Optional

from koji import MultiCallSession, VirtualCall
from pydantic import Field

from .base import BaseKojiObject, BaseKey
from .change import ChangeReport, Change


@dataclass
class HostCreate(Change):
    name: str
    arches: List[str]

    def impl_apply(self, session: MultiCallSession):
        return session.createHost(
            self.name,
            arches=' '.join(self.arches))


@dataclass
class HostSetArches(Change):
    name: str
    arches: List[str]

    def impl_apply(self, session: MultiCallSession):
        return session.editHost(self.name, arches=' '.join(self.arches))


@dataclass
class HostSetCapacity(Change):
    name: str
    capacity: float

    def impl_apply(self, session: MultiCallSession):
        return session.editHost(self.name, capacity=self.capacity)


@dataclass
class HostSetEnabled(Change):
    name: str
    enabled: bool

    def impl_apply(self, session: MultiCallSession):
        return session.editHost(self.name, enabled=self.enabled)


@dataclass
class HostSetDescription(Change):
    name: str
    description: str

    def impl_apply(self, session: MultiCallSession):
        return session.editHost(self.name, description=self.description)


@dataclass
class HostAddChannel(Change):
    name: str
    channel: str

    def impl_apply(self, session: MultiCallSession):
        return session.addHostToChannel(self.name, self.channel)


@dataclass
class HostRemoveChannel(Change):
    name: str
    channel: str

    def impl_apply(self, session: MultiCallSession):
        return session.removeHostFromChannel(self.name, self.channel)


class HostChangeReport(ChangeReport):

    def create_host(self):
        self.add(HostCreate(self.obj.name, self.obj.arches))

    def set_host_arches(self):
        self.add(HostSetArches(self.obj.name, self.obj.arches))

    def set_host_capacity(self):
        self.add(HostSetCapacity(self.obj.name, self.obj.capacity))

    def set_host_enabled(self):
        self.add(HostSetEnabled(self.obj.name, self.obj.enabled))

    def set_host_description(self):
        self.add(HostSetDescription(self.obj.name, self.obj.description))

    def add_host_channel(self, channel: str):
        self.add(HostAddChannel(self.obj.name, channel))

    def remove_host_channel(self, channel: str):
        self.add(HostRemoveChannel(self.obj.name, channel))

    def impl_read(self, session: MultiCallSession):
        self._hostinfo: VirtualCall = session.getHost(self.obj.name)

    def impl_compare(self):
        info = self._hostinfo.result
        if not info:
            self.create_host()
            if self.obj.capacity is not None:
                self.set_host_capacity()
            if self.obj.enabled is not None and not self.obj.enabled:
                self.set_host_enabled()
            if self.obj.description is not None:
                self.set_host_description()
            for channel in self.obj.channels:
                self.add_host_channel(channel)
            return

        arches = set(info['arches'].split())
        if arches != set(self.obj.arches):
            self.set_host_arches()
        if self.obj.capacity is not None and info['capacity'] != self.obj.capacity:
            self.set_host_capacity()
        if info['enabled'] != self.obj.enabled:
            self.set_host_enabled()
        if self.obj.description is not None and info['description'] != self.obj.description:
            self.set_host_description()

        channels = info['channels']
        for channel in self.obj.channels:
            if channel not in channels:
                self.add_host_channel(channel)

        if self.obj.exact_channels:
            for channel in channels:
                if channel not in self.obj.channels:
                    self.remove_host_channel(channel)


class Host(BaseKojiObject):
    """
    Koji build host object model.
    """

    typename: ClassVar[str] = "host"
    _can_split: ClassVar[bool] = True

    arches: List[str] = Field(alias='arches', default_factory=list)
    capacity: Optional[float] = Field(alias='capacity', default=None)
    enabled: bool = Field(alias='enabled', default=True)
    description: Optional[str] = Field(alias='description', default=None)
    channels: List[str] = Field(alias='channels', default_factory=list)
    exact_channels: bool = Field(alias='exact-channels', default=False)


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


    def change_report(host: 'Host') -> HostChangeReport:
        return HostChangeReport(host)


# The end.

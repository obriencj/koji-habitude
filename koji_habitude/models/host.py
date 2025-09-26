"""
koji-habitude - models.host

Host model for koji build host objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""


from dataclasses import dataclass
from typing import ClassVar, List, Sequence

from koji import ClientSession, VirtualCall
from pydantic import Field

from .base import BaseKojiObject, BaseKey
from .change import ChangeReport, Change


@dataclass
class HostCreate(Change):
    name: str
    arches: List[str]
    capacity: float
    enabled: bool
    description: str
    channels: List[str]


@dataclass
class HostSetArches(Change):
    name: str
    arches: List[str]

    def impl_apply(self, session: ClientSession):
        return session.editHost(self.name, arches=' '.join(self.arches))


@dataclass
class HostSetCapacity(Change):
    name: str
    capacity: float

    def impl_apply(self, session: ClientSession):
        return session.editHost(self.name, capacity=self.capacity)

@dataclass
class HostSetEnabled(Change):
    name: str
    enabled: bool

    def impl_apply(self, session: ClientSession):
        return session.editHost(self.name, enabled=self.enabled)


@dataclass
class HostSetDescription(Change):
    name: str
    description: str

    def impl_apply(self, session: ClientSession):
        return session.editHost(self.name, description=self.description)


@dataclass
class HostAddChannel(Change):
    name: str
    channel: str

    def impl_apply(self, session: ClientSession):
        return session.addHostChannel(self.name, self.channel)


@dataclass
class HostRemoveChannel(Change):
    name: str
    channel: str

    def impl_apply(self, session: ClientSession):
        return session.removeHostChannel(self.name, self.channel)


class HostChangeReport(ChangeReport):

    def create_host(self):
        self.add(HostCreate(self.obj.name, self.obj.arches, self.obj.capacity, self.obj.enabled, self.obj.description, self.obj.channels))

    def set_host_arches(self):
        self.add(HostSetArches(self.obj.name, self.obj.arches))

    def set_host_capacity(self):
        self.add(HostSetCapacity(self.obj.name, self.obj.capacity))

    def set_host_enabled(self):
        self.add(HostSetEnabled(self.obj.name, self.obj.enabled))

    def set_host_description(self):
        self.add(HostSetDescription(self.obj.name, self.obj.description))

    def add_host_channel(self):
        self.add(HostAddChannel(self.obj.name, self.obj.channel))

    def remove_host_channel(self):
        self.add(HostRemoveChannel(self.obj.name, self.obj.channel))

    def impl_read(self, session: ClientSession):
        self._hostinfo: VirtualCall = session.getHost(self.obj.name)

    def impl_compare(self):
        info = self._hostinfo.result
        if not info:
            self.create_host()
            return

class Host(BaseKojiObject):
    """
    Koji build host object model.
    """

    typename: ClassVar[str] = "host"
    _can_split: ClassVar[bool] = True

    arches: List[str] = Field(alias='arches', default_factory=list)
    capacity: float = Field(alias='capacity', default=0.0)
    enabled: bool = Field(alias='enabled', default=True)
    description: str = Field(alias='description', default='')
    channels: List[str] = Field(alias='channels', default_factory=list)


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


# The end.

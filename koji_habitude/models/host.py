"""
koji-habitude - models.host

Host model for koji build host objects.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated with Human Rework


from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, Dict, List, Optional, Sequence

from koji import MultiCallSession, VirtualCall

from ..koji import call_processor
from .base import BaseKey, CoreModel, CoreObject, RemoteObject
from .change import Add, ChangeReport, Create, Remove, Update
from .compat import Field

if TYPE_CHECKING:
    from ..resolver import Resolver


@dataclass
class HostCreate(Create):
    obj: 'Host'

    def impl_apply(self, session: MultiCallSession):
        return session.createHost(
            self.obj.name,
            arches=' '.join(self.obj.arches))

    def summary(self) -> str:
        arches_str = ', '.join(self.obj.arches)
        return f"Create host {self.obj.name} with arches [{arches_str}]"


@dataclass
class HostSetArches(Update):
    obj: 'Host'
    arches: List[str]

    def impl_apply(self, session: MultiCallSession):
        return session.editHost(self.obj.name, arches=' '.join(self.arches))

    def summary(self) -> str:
        arches_str = ', '.join(self.arches)
        return f"Set arches to [{arches_str}]"


@dataclass
class HostSetCapacity(Update):
    obj: 'Host'
    capacity: float

    def impl_apply(self, session: MultiCallSession):
        return session.editHost(self.obj.name, capacity=self.capacity)

    def summary(self) -> str:
        return f"Set capacity to {self.capacity}"


@dataclass
class HostSetEnabled(Update):
    obj: 'Host'
    enabled: bool

    def impl_apply(self, session: MultiCallSession):
        return session.editHost(self.obj.name, enabled=self.enabled)

    def summary(self) -> str:
        action = "Enable" if self.enabled else "Disable"
        return f"{action} host"


@dataclass
class HostSetDescription(Update):
    obj: 'Host'
    description: str

    def impl_apply(self, session: MultiCallSession):
        return session.editHost(self.obj.name, description=self.description)

    def summary(self) -> str:
        return f"Set description to '{self.description}'"


@dataclass
class HostAddChannel(Add):
    obj: 'Host'
    channel: str

    _skippable: ClassVar[bool] = True

    def skip_check_impl(self, resolver: 'Resolver') -> bool:
        channel = resolver.resolve(('channel', self.channel))
        return channel.is_phantom()

    def impl_apply(self, session: MultiCallSession):
        return session.addHostToChannel(self.obj.name, self.channel)

    def summary(self) -> str:
        return f"Add channel '{self.channel}'"


@dataclass
class HostRemoveChannel(Remove):
    obj: 'Host'
    channel: str

    def impl_apply(self, session: MultiCallSession):
        return session.removeHostFromChannel(self.obj.name, self.channel)

    def summary(self) -> str:
        return f"Remove channel '{self.channel}'"


class HostChangeReport(ChangeReport):

    def impl_compare(self):
        remote = self.obj.remote()
        if not remote:
            if not self.obj.was_split():
                # we don't exist, and we didn't split our create to an earlier
                # call, so create now.
                yield HostCreate(self.obj)

            if self.obj.is_split():
                return

            if self.obj.capacity is not None:
                yield HostSetCapacity(self.obj, self.obj.capacity)
            if self.obj.enabled is not None and not self.obj.enabled:
                yield HostSetEnabled(self.obj, self.obj.enabled)
            if self.obj.description is not None:
                yield HostSetDescription(self.obj, self.obj.description)
            for channel in self.obj.channels:
                yield HostAddChannel(self.obj, channel)
            return

        if self.obj.is_split():
            return

        if set(remote.arches) != set(self.obj.arches):
            yield HostSetArches(self.obj, self.obj.arches)
        if self.obj.capacity is not None and remote.capacity != self.obj.capacity:
            yield HostSetCapacity(self.obj, self.obj.capacity)
        if remote.enabled != self.obj.enabled:
            yield HostSetEnabled(self.obj, self.obj.enabled)
        if self.obj.description is not None and remote.description != self.obj.description:
            yield HostSetDescription(self.obj, self.obj.description)

        channels = remote.channels
        for channel in self.obj.channels:
            if channel not in channels:
                yield HostAddChannel(self.obj, channel)

        if self.obj.exact_channels:
            for channel in channels:
                if channel not in self.obj.channels:
                    yield HostRemoveChannel(self.obj, channel)


class HostModel(CoreModel):
    """Field definitions for Host objects"""

    typename: ClassVar[str] = "host"

    arches: List[str] = Field(alias='arches', default_factory=list)
    capacity: Optional[float] = Field(alias='capacity', default=None)
    enabled: bool = Field(alias='enabled', default=True)
    description: Optional[str] = Field(alias='description', default=None)
    channels: List[str] = Field(alias='channels', default_factory=list)


    def dependency_keys(self) -> Sequence[BaseKey]:
        """
        Return dependencies for this host.
        """
        return [('channel', channel) for channel in self.channels]


class Host(HostModel, CoreObject):
    """
    Local host object from YAML.
    """

    exact_channels: bool = Field(alias='exact-channels', default=False)

    _auto_split: ClassVar[bool] = True


    def split(self) -> 'Host':
        child = Host(
            name=self.name,
            arches=self.arches,
            capacity=self.capacity,
            enabled=self.enabled,
            description=self.description)
        child._is_split = True
        self._was_split = True
        return child


    def change_report(self, resolver: 'Resolver') -> HostChangeReport:
        return HostChangeReport(self, resolver)


    @classmethod
    def query_remote(cls, session: MultiCallSession, key: BaseKey) -> 'VirtualCall[RemoteHost]':
        return call_processor(RemoteHost.from_koji, session.getHost, key[1], strict=False)


class RemoteHost(HostModel, RemoteObject):
    """
    Remote host object from Koji API
    """

    @classmethod
    def from_koji(cls, data: Optional[Dict[str, Any]]):
        if data is None:
            return None

        return cls(
            koji_id=data['id'],
            name=data['name'],
            arches=data.get('arches', '').split(),
            capacity=data.get('capacity'),
            enabled=data.get('enabled', True),
            description=data.get('description'),
            channels=data.get('channels', []),
        )


# The end.

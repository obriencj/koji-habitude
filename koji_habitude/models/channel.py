"""
koji-habitude - models.channel

Channel model for koji channel objects.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated with Human Rework


from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, Dict, List, Optional

from koji import MultiCallSession, VirtualCall

from ..koji import call_processor, promise_call
from .base import BaseKey, CoreModel, CoreObject, RemoteObject
from .change import Add, ChangeReport, Create, Remove, Update
from .compat import Field

if TYPE_CHECKING:
    from ..resolver import Resolver


@dataclass
class ChannelCreate(Create):
    obj: 'Channel'

    def impl_apply(self, session: MultiCallSession):
        return session.createChannel(self.obj.name, self.obj.description)

    def summary(self) -> str:
        desc_info = f" with description {self.obj.description!r}" if self.obj.description else ""
        return f"Create channel {self.obj.name}{desc_info}"


@dataclass
class ChannelSetDescription(Update):
    obj: 'Channel'
    description: Optional[str]

    def impl_apply(self, session: MultiCallSession):
        return session.editChannel(self.obj.name, description=self.description)

    def summary(self) -> str:
        if self.description:
            return f"Set description to {self.description!r}"
        else:
            return "Clear description"


@dataclass
class ChannelAddHost(Add):
    obj: 'Channel'
    host: str

    _skippable: ClassVar[bool] = True

    def skip_check_impl(self, resolver: 'Resolver') -> bool:
        host = resolver.resolve(('host', self.host))
        return host.is_phantom()

    def impl_apply(self, session: MultiCallSession):
        return session.addHostToChannel(self.host, self.obj.name)

    def summary(self) -> str:
        return f"Add host {self.host}"


@dataclass
class ChannelRemoveHost(Remove):
    obj: 'Channel'
    host: str

    def impl_apply(self, session: MultiCallSession):
        return session.removeHostFromChannel(self.host, self.obj.name)

    def summary(self) -> str:
        return f"Remove host {self.host}"


class ChannelChangeReport(ChangeReport):
    """
    Change report for channel objects.
    """

    def impl_compare(self):
        remote = self.obj.remote()
        if not remote:
            if not self.obj.was_split():
                # we don't exist, and we didn't split our create to an earlier
                # call, so create now.
                yield ChannelCreate(self.obj)

            if self.obj.is_split():
                return

            for host in self.obj.hosts:
                yield ChannelAddHost(self.obj, host)
            return

        if self.obj.is_split():
            return

        if self.obj.description is not None and remote.description != self.obj.description:
            yield ChannelSetDescription(self.obj, self.obj.description)

        hosts = remote.hosts
        for host in self.obj.hosts:
            if host not in hosts:
                yield ChannelAddHost(self.obj, host)

        if self.obj.exact_hosts:
            for host in hosts:
                if host not in self.obj.hosts:
                    yield ChannelRemoveHost(self.obj, host)


class ChannelModel(CoreModel):
    """
    Field definitions for Channel objects
    """

    typename: ClassVar[str] = "channel"

    description: Optional[str] = Field(alias='description', default=None)
    hosts: List[str] = Field(alias='hosts', default_factory=list)


    def dependency_keys(self) -> List[BaseKey]:
        return [('host', host) for host in self.hosts]


class Channel(ChannelModel, CoreObject):
    """
    Local channel object from YAML.
    """

    exact_hosts: bool = Field(alias='exact-hosts', default=False)

    _auto_split: ClassVar[bool] = True


    def change_report(self, resolver: 'Resolver') -> ChannelChangeReport:
        return ChannelChangeReport(self, resolver)


    @classmethod
    def query_remote(cls, session: MultiCallSession, key: BaseKey) -> 'VirtualCall[RemoteChannel]':
        return call_processor(RemoteChannel.from_koji, session.getChannel, key[1], strict=False)


class RemoteChannel(ChannelModel, RemoteObject):
    """
    Remote channel object from Koji API
    """

    @classmethod
    def from_koji(cls, data: Optional[Dict[str, Any]]):
        if data is None:
            return None

        return cls(
            koji_id=data['id'],
            name=data['name'],
            description=data.get('description'),
        )


    def set_koji_hosts(self, result):
        self.hosts = [host['name'] for host in result.result]


    def load_additional_data(self, session: MultiCallSession):
        promise_call(self.set_koji_hosts, session.listHosts, channelID=self.name)


# The end.

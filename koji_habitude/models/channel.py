"""
koji-habitude - models.channel

Channel model for koji channel objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated with Human Rework


from dataclasses import dataclass
from typing import ClassVar, List, Optional, Any, TYPE_CHECKING

from koji import ClientSession, MultiCallSession, VirtualCall
from pydantic import Field

from .base import BaseObject, BaseKey
from .change import ChangeReport, Change, Create, Update, Add, Remove

if TYPE_CHECKING:
    from ..resolver import Resolver


@dataclass
class ChannelCreate(Create):
    name: str
    description: Optional[str] = None

    def impl_apply(self, session: MultiCallSession):
        return session.createChannel(self.name, self.description)

    def explain(self) -> str:
        desc_info = f" with description '{self.description}'" if self.description else ""
        return f"Create channel '{self.name}'{desc_info}"


@dataclass
class ChannelSetDescription(Update):
    name: str
    description: Optional[str] = None

    def impl_apply(self, session: MultiCallSession):
        return session.editChannel(self.name, description=self.description)

    def explain(self) -> str:
        if self.description:
            return f"Set description for channel '{self.name}' to '{self.description}'"
        else:
            return f"Remove description from channel '{self.name}'"


@dataclass
class ChannelAddHost(Add):
    name: str
    host: str

    _skippable: ClassVar[bool] = True

    def skip_check_impl(self, resolver: 'Resolver') -> bool:
        host = resolver.resolve(('host', self.host))
        return host.is_phantom()

    def impl_apply(self, session: MultiCallSession):
        return session.addHostToChannel(self.host, self.name)

    def explain(self) -> str:
        return f"Add host '{self.host}' to channel '{self.name}'"


@dataclass
class ChannelRemoveHost(Remove):
    name: str
    host: str

    def impl_apply(self, session: MultiCallSession):
        return session.removeHostFromChannel(self.host, self.name)

    def explain(self) -> str:
        return f"Remove host '{self.host}' from channel '{self.name}'"


class ChannelChangeReport(ChangeReport):
    """
    Change report for channel objects.
    """

    def impl_read(self, session: MultiCallSession):
        self._channelinfo: VirtualCall = self.obj.query_exists(session)
        self._hosts: VirtualCall = session.listHosts(channelID=self.obj.name)


    def impl_compare(self):
        info = self._channelinfo.result
        if not info:
            if not self.obj.was_split():
                # we don't exist, and we didn't split our create to an earlier
                # call, so create now.
                yield ChannelCreate(self.obj.name, self.obj.description)

            if self.obj.is_split():
                return

            for host in self.obj.hosts:
                yield ChannelAddHost(self.obj.name, host)
            return

        if self.obj.is_split():
            return

        if self.obj.description is not None and info['description'] != self.obj.description:
            yield ChannelSetDescription(self.obj.name, self.obj.description)

        hosts = {host['name']: host for host in self._hosts.result}
        for host in self.obj.hosts:
            if host not in hosts:
                yield ChannelAddHost(self.obj.name, host)

        if self.obj.exact_hosts:
            for host in hosts:
                if host not in self.obj.hosts:
                    yield ChannelRemoveHost(self.obj.name, host)


class Channel(BaseObject):
    """
    Koji channel object model.
    """

    typename: ClassVar[str] = "channel"

    description: Optional[str] = Field(alias='description', default=None)
    hosts: List[str] = Field(alias='hosts', default_factory=list)
    exact_hosts: bool = Field(alias='exact-hosts', default=False)

    _auto_split: ClassVar[bool] = True


    def dependency_keys(self) -> List[BaseKey]:
        """
        Channels can depend on:
        - Hosts
        """

        return [('host', host) for host in self.hosts]


    def change_report(self, resolver: 'Resolver') -> ChannelChangeReport:
        return ChannelChangeReport(self, resolver)


    @classmethod
    def check_exists(cls, session: ClientSession, key: BaseKey) -> Any:
        return session.getChannel(key[1], strict=False)


# The end.

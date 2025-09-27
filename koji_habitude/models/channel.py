"""
koji-habitude - models.channel

Channel model for koji channel objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""


from dataclasses import dataclass
from typing import ClassVar, List, Optional

from koji import MultiCallSession, VirtualCall
from pydantic import Field

from .base import BaseKojiObject, BaseKey
from .change import ChangeReport, Change


@dataclass
class ChannelCreate(Change):
    name: str
    description: Optional[str] = None

    def impl_apply(self, session: MultiCallSession):
        return session.createChannel(self.name, self.description)

    def explain(self) -> str:
        desc_info = f" with description '{self.description}'" if self.description else ""
        return f"Create channel '{self.name}'{desc_info}"


@dataclass
class ChannelSetDescription(Change):
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
class ChannelAddHost(Change):
    name: str
    host: str

    def impl_apply(self, session: MultiCallSession):
        return session.addHostToChannel(self.host, self.name)

    def explain(self) -> str:
        return f"Add host '{self.host}' to channel '{self.name}'"


@dataclass
class ChannelRemoveHost(Change):
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

    def create_channel(self):
        self.add(ChannelCreate(self.obj.name, self.obj.description))

    def set_description(self):
        self.add(ChannelSetDescription(self.obj.name, self.obj.description))

    def add_host(self, host: str):
        self.add(ChannelAddHost(self.obj.name, host))

    def remove_host(self, host: str):
        self.add(ChannelRemoveHost(self.obj.name, host))


    def impl_read(self, session: MultiCallSession):
        self._channelinfo: VirtualCall = session.getChannel(self.obj.name, strict=False)
        self._hosts: VirtualCall = session.listHosts(channelID=self.obj.name)


    def impl_compare(self):
        info = self._channelinfo.result
        if not info:
            self.create_channel()
            for host in self.obj.hosts:
                self.add_host(host)
            return

        if self.obj.description is not None and info['description'] != self.obj.description:
            self.set_description()

        hosts = {host['name']: host for host in self._hosts.result}
        for host in self.obj.hosts:
            if host not in hosts:
                self.add_host(host)

        if self.obj.exact_hosts:
            for host in hosts:
                if host not in self.obj.hosts:
                    self.remove_host(host)


class Channel(BaseKojiObject):
    """
    Koji channel object model.
    """

    typename: ClassVar[str] = "channel"
    _can_split: ClassVar[bool] = True

    description: Optional[str] = Field(alias='description', default=None)
    hosts: List[str] = Field(alias='hosts', default_factory=list)
    exact_hosts: bool = Field(alias='exact-hosts', default=False)


    def dependency_keys(self) -> List[BaseKey]:
        """
        Channels can depend on:
        - Hosts
        """

        return [('host', host) for host in self.hosts]


    def change_report(self) -> ChannelChangeReport:
        return ChannelChangeReport(self)


# The end.

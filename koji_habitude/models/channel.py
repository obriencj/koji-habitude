"""
koji-habitude - models.channel

Channel model for koji channel objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""


from typing import ClassVar, List, Tuple

from pydantic import Field

from .base import BaseKojiObject


class Channel(BaseKojiObject):
    """
    Koji channel object model.
    """

    typename: ClassVar[str] = "channel"
    _can_split: ClassVar[bool] = True

    hosts: List[str] = Field(alias='hosts', default_factory=list)


    def dependency_keys(self) -> List[Tuple[str, str]]:
        """
        Return dependencies for this channel.
        """

        return [('host', host) for host in self.hosts]


# The end.

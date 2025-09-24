"""
koji-habitude - models.host

Host model for koji build host objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""


from typing import ClassVar, List, Tuple, Optional

from pydantic import Field

from .base import BaseKojiObject, BaseKey


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


    def split(self) -> Optional['Host']:
        return Host(
            name=self.name,
            arches=self.arches,
            capacity=self.capacity,
            enabled=self.enabled,
            description=self.description)


    def dependency_keys(self) -> List[BaseKey]:
        """
        Return dependencies for this host.
        """
        return [('channel', channel) for channel in self.channels]


# The end.

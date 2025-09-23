"""
koji-habitude - models.group

Group model for koji group objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

from typing import ClassVar, List, Tuple

from pydantic import Field

from .base import BaseKojiObject

class Group(BaseKojiObject):
    """
    Koji group object model.
    """

    typename: ClassVar[str] = "group"
    _can_split: ClassVar[bool] = True

    members: List[str] = Field(alias='members', default_factory=list)
    permissions: List[str] = Field(alias='permissions', default_factory=list)


    def dependency_keys(self) -> List[Tuple[str, str]]:
        """
        Return dependencies for this group.

        Groups may depend on:
        - Users
        - Permissions
        """

        deps = []

        for member in self.members:
            deps.append(('user', member))

        for permission in self.permissions:
            deps.append(('permission', permission))

        return deps


# The end.

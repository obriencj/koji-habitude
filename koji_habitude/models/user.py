"""
koji-habitude - models.user

User model for koji user objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

from typing import ClassVar, List, Optional

from pydantic import Field

from .base import BaseKojiObject, BaseKey


class User(BaseKojiObject):
    """
    Koji user object model.
    """

    typename: ClassVar[str] = "user"
    _can_split: ClassVar[bool] = True

    groups: List[str] = Field(alias='groups', default_factory=list)
    permissions: List[str] = Field(alias='permissions', default_factory=list)
    enabled: bool = Field(alias='enabled', default=True)


    def split(self) -> 'User':
        return User(name=self.name, enabled=self.enabled)


    def dependency_keys(self) -> List[BaseKey]:
        """
        Users can depend on:
        - Groups
        - Permissions
        """

        deps: List[BaseKey] = []

        for group in self.groups:
            deps.append(('group', group))

        for permission in self.permissions:
            deps.append(('permission', permission))

        return deps


# The end.

"""
koji-habitude - models.user

User model for koji user objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

from typing import ClassVar, List, Tuple, Optional

from pydantic import Field

from .base import BaseKojiObject


class User(BaseKojiObject):
    """
    Koji user object model.
    """

    typename: ClassVar[str] = "user"
    _can_split: ClassVar[bool] = True

    groups: List[str] = Field(alias='groups', default_factory=list)
    permissions: List[str] = Field(alias='permissions', default_factory=list)
    enabled: bool = Field(alias='enabled', default=True)


    def split(self) -> Optional['User']:
        return User(name=self.name, enabled=self.enabled)


    def dependency_keys(self) -> List[Tuple[str, str]]:
        """
        Return dependencies for this user.

        Users typically have no dependencies on other koji objects.
        They are usually leaf nodes in the dependency tree.
        """

        deps = []

        for group in self.groups:
            deps.append(('group', group))

        for permission in self.permissions:
            deps.append(('permission', permission))

        return deps


# The end.

"""
koji-habitude - models.group

Group model for koji group objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

from typing import Dict, List, Tuple, Any
from .base import BaseKojiObject


class Group(BaseKojiObject):
    """
    Koji group object model.
    """

    typename = "group"

    _can_split = True


    def dependent_keys(self) -> List[Tuple[str, str]]:
        """
        Return dependencies for this group.

        Groups may depend on:
        - Tags (for tag-specific group configurations)
        - Users (for group membership)
        """

        deps = []

        # Tag dependency if this is a tag-specific group
        tag = self.data.get('tag')
        if tag:
            deps.append(('tag', tag))

        # User dependencies for group members
        members = self.data.get('members', [])
        if isinstance(members, list):
            for member in members:
                if isinstance(member, dict) and 'name' in member:
                    deps.append(('user', member['name']))
                elif isinstance(member, str):
                    deps.append(('user', member))

        return deps

# The end.

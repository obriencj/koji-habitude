"""
koji-habitude - models.group

Group model for koji group objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated with Human Rework


from dataclasses import dataclass
from typing import ClassVar, List, Tuple, Any, TYPE_CHECKING

from koji import ClientSession, MultiCallSession, VirtualCall
from pydantic import Field

from .base import BaseObject, BaseKey
from .change import Change, ChangeReport

if TYPE_CHECKING:
    from ..resolver import Resolver


@dataclass
class GroupCreate(Change):
    name: str

    def impl_apply(self, session: MultiCallSession):
        return session.newGroup(self.name)

    def explain(self) -> str:
        return f"Create group '{self.name}'"


@dataclass
class GroupEnable(Change):
    name: str

    def impl_apply(self, session: MultiCallSession):
        return session.enableUser(self.name)

    def explain(self) -> str:
        return f"Enable group '{self.name}'"


@dataclass
class GroupDisable(Change):
    name: str

    def impl_apply(self, session: MultiCallSession):
        return session.disableUser(self.name)

    def explain(self) -> str:
        return f"Disable group '{self.name}'"


@dataclass
class GroupAddMember(Change):
    name: str
    member: str

    def impl_apply(self, session: MultiCallSession):
        return session.addGroupMember(self.name, self.member)

    def explain(self) -> str:
        return f"Add member '{self.member}' to group '{self.name}'"


@dataclass
class GroupRemoveMember(Change):
    name: str
    member: str

    def impl_apply(self, session: MultiCallSession):
        return session.dropGroupMember(self.name, self.member)

    def explain(self) -> str:
        return f"Remove member '{self.member}' from group '{self.name}'"


@dataclass
class GroupAddPermission(Change):
    name: str
    permission: str

    def impl_apply(self, session: MultiCallSession):
        return session.grantPermission(self.name, self.permission, create=True)

    def explain(self) -> str:
        return f"Grant permission '{self.permission}' to group '{self.name}'"


@dataclass
class GroupRemovePermission(Change):
    name: str
    permission: str

    def impl_apply(self, session: MultiCallSession):
        return session.revokePermission(self.name, self.permission)

    def explain(self) -> str:
        return f"Revoke permission '{self.permission}' from group '{self.name}'"


class GroupChangeReport(ChangeReport):

    def impl_read(self, session: MultiCallSession):
        self._groupinfo: VirtualCall = self.obj.query_exists(session)
        self._members: VirtualCall = None
        self._permissions: VirtualCall = None
        return self.impl_read_defer


    def impl_read_defer(self, session: MultiCallSession):
        if self._groupinfo.result is None:
            return
        self._members: VirtualCall = session.getGroupMembers(self.obj.name)
        self._permissions: VirtualCall = session.getUserPerms(self.obj.name)


    def impl_compare(self):
        info = self._groupinfo.result
        if not info:
            if not self.obj.was_split():
                # we don't exist, and we didn't split our create to an earlier
                # call, so create now.
                yield GroupCreate(self.obj.name)

            for member in self.obj.members:
                yield GroupAddMember(self.obj.name, member)
            for permission in self.obj.permissions:
                yield GroupAddPermission(self.obj.name, permission)
            return

        if info['status'] != (0 if self.obj.enabled else 1):
            if self.obj.enabled:
                yield GroupEnable(self.obj.name)
            else:
                yield GroupDisable(self.obj.name)

        members = { m['name']: m for m in self._members.result }
        for member in self.obj.members:
            if member not in members:
                yield GroupAddMember(self.obj.name, member)

        if self.obj.exact_members:
            for member in members:
                if member not in self.obj.members:
                    yield GroupRemoveMember(self.obj.name, member)

        permissions = self._permissions.result
        for permission in self.obj.permissions:
            if permission not in permissions:
                yield GroupAddPermission(self.obj.name, permission)

        if self.obj.exact_permissions:
            for permission in permissions:
                if permission not in self.obj.permissions:
                    yield GroupRemovePermission(self.obj.name, permission)


class Group(BaseObject):
    """
    Koji group object model.
    """

    typename: ClassVar[str] = "group"

    enabled: bool = Field(alias='enabled', default=True)
    members: List[str] = Field(alias='members', default_factory=list)
    permissions: List[str] = Field(alias='permissions', default_factory=list)

    exact_members: bool = Field(alias='exact-members', default=False)
    exact_permissions: bool = Field(alias='exact-permissions', default=False)

    _auto_split: ClassVar[bool] = True


    def dependency_keys(self) -> List[BaseKey]:
        """
        Return dependencies for this group.

        Groups may depend on:
        - Users
        - Permissions
        """

        deps: List[BaseKey] = []

        for member in self.members:
            deps.append(('user', member))

        for permission in self.permissions:
            deps.append(('permission', permission))

        return deps


    def change_report(self, resolver: 'Resolver') -> GroupChangeReport:
        return GroupChangeReport(self, resolver)


    @classmethod
    def check_exists(cls, session: ClientSession, key: BaseKey) -> Any:
        return session.getUser(key[1], strict=False)


# The end.

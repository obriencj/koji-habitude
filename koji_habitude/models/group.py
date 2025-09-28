"""
koji-habitude - models.group

Group model for koji group objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

from dataclasses import dataclass
from typing import ClassVar, List, Tuple, Any

from koji import ClientSession, MultiCallSession, VirtualCall
from pydantic import Field

from .base import BaseKojiObject, BaseKey
from .change import Change, ChangeReport


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

    def create_group(self):
        self.add(GroupCreate(self.obj.name))

    def enable_group(self):
        self.add(GroupEnable(self.obj.name))

    def disable_group(self):
        self.add(GroupDisable(self.obj.name))

    def add_member(self, member: str):
        self.add(GroupAddMember(self.obj.name, member))

    def remove_member(self, member: str):
        self.add(GroupRemoveMember(self.obj.name, member))

    def add_permission(self, permission: str):
        self.add(GroupAddPermission(self.obj.name, permission))

    def remove_permission(self, permission: str):
        self.add(GroupRemovePermission(self.obj.name, permission))


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
            self.create_group()
            for member in self.obj.members:
                self.add_member(member)
            for permission in self.obj.permissions:
                self.add_permission(permission)
            return

        if info['status'] != self.obj.enabled:
            if self.obj.enabled:
                self.enable_group()
            else:
                self.disable_group()

        members = { m['name']: m for m in self._members.result }
        for member in self.obj.members:
            if member not in members:
                self.add_member(member)
        for member in members:
            if member not in self.obj.members:
                self.remove_member(member)

        permissions = self._permissions.result
        for permission in self.obj.permissions:
            if permission not in permissions:
                self.add_permission(permission)
        for permission in permissions:
            if permission not in self.obj.permissions:
                self.remove_permission(permission)


class Group(BaseKojiObject):
    """
    Koji group object model.
    """

    typename: ClassVar[str] = "group"
    _can_split: ClassVar[bool] = True

    enabled: bool = Field(alias='enabled', default=True)
    members: List[str] = Field(alias='members', default_factory=list)
    permissions: List[str] = Field(alias='permissions', default_factory=list)


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


    def change_report(self) -> GroupChangeReport:
        return GroupChangeReport(self)


    @classmethod
    def check_exists(cls, session: ClientSession, key: BaseKey) -> Any:
        return session.getUser(key[1], strict=False)


# The end.

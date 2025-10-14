"""
koji-habitude - models.group

Group model for koji group objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated with Human Rework


from dataclasses import dataclass
from typing import Any, ClassVar, List, TYPE_CHECKING

from koji import MultiCallSession, VirtualCall

from ..pydantic import Field

from .base import BaseKey, BaseObject
from .change import Add, ChangeReport, Create, Remove, Update

if TYPE_CHECKING:
    from ..resolver import Resolver


@dataclass
class GroupCreate(Create):
    obj: 'Group'

    def impl_apply(self, session: MultiCallSession):
        return session.newGroup(self.obj.name)

    def summary(self) -> str:
        return f"Create group {self.obj.name}"


@dataclass
class GroupEnable(Update):
    obj: 'Group'

    def impl_apply(self, session: MultiCallSession):
        return session.enableUser(self.obj.name)

    def summary(self) -> str:
        return "Enable group"


@dataclass
class GroupDisable(Update):
    obj: 'Group'

    def impl_apply(self, session: MultiCallSession):
        return session.disableUser(self.obj.name)

    def summary(self) -> str:
        return "Disable group"


@dataclass
class GroupAddMember(Add):
    obj: 'Group'
    member: str

    _skippable: ClassVar[bool] = True

    def skip_check_impl(self, resolver: 'Resolver') -> bool:
        member = resolver.resolve(('user', self.member))
        return member.is_phantom()

    def impl_apply(self, session: MultiCallSession):
        return session.addGroupMember(self.obj.name, self.member)

    def summary(self) -> str:
        return f"Add member {self.member}"


@dataclass
class GroupRemoveMember(Remove):
    obj: 'Group'
    member: str

    def impl_apply(self, session: MultiCallSession):
        return session.dropGroupMember(self.obj.name, self.member)

    def summary(self) -> str:
        return f"Remove member {self.member}"


@dataclass
class GroupAddPermission(Add):
    obj: 'Group'
    permission: str

    _skippable: ClassVar[bool] = True

    def skip_check_impl(self, resolver: 'Resolver') -> bool:
        permission = resolver.resolve(('permission', self.permission))
        return permission.is_phantom()

    def impl_apply(self, session: MultiCallSession):
        return session.grantPermission(self.obj.name, self.permission, create=True)

    def summary(self) -> str:
        return f"Grant permission {self.permission}"


@dataclass
class GroupRemovePermission(Remove):
    obj: 'Group'
    permission: str

    def impl_apply(self, session: MultiCallSession):
        return session.revokePermission(self.obj.name, self.permission)

    def summary(self) -> str:
        return f"Revoke permission {self.permission}"


class GroupChangeReport(ChangeReport):

    def impl_read(self, session: MultiCallSession):
        self._groupinfo: VirtualCall = self.obj.query_exists(session)
        self._members: VirtualCall = None
        self._permissions: VirtualCall = None
        return self.impl_read_defer


    def impl_read_defer(self, session: MultiCallSession):
        if self._groupinfo.result is None:
            return
        self._members = session.getGroupMembers(self.obj.name)
        self._permissions = session.getUserPerms(self.obj.name)


    def impl_compare(self):
        info = self._groupinfo.result
        if not info:
            if not self.obj.was_split():
                # we don't exist, and we didn't split our create to an earlier
                # call, so create now.
                yield GroupCreate(self.obj)

            if self.obj.is_split():
                return

            for member in self.obj.members:
                yield GroupAddMember(self.obj, member)
            for permission in self.obj.permissions:
                yield GroupAddPermission(self.obj, permission)
            return

        if self.obj.is_split():
            return

        if info['status'] != (0 if self.obj.enabled else 1):
            if self.obj.enabled:
                yield GroupEnable(self.obj)
            else:
                yield GroupDisable(self.obj)

        members = {m['name']: m for m in self._members.result}
        for member in self.obj.members:
            if member not in members:
                yield GroupAddMember(self.obj, member)

        if self.obj.exact_members:
            for member in members:
                if member not in self.obj.members:
                    yield GroupRemoveMember(self.obj, member)

        permissions = self._permissions.result
        for permission in self.obj.permissions:
            if permission not in permissions:
                yield GroupAddPermission(self.obj, permission)

        if self.obj.exact_permissions:
            for permission in permissions:
                if permission not in self.obj.permissions:
                    yield GroupRemovePermission(self.obj, permission)


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
    def check_exists(cls, session: MultiCallSession, key: BaseKey) -> VirtualCall:
        return session.getUser(key[1], strict=False)


# The end.

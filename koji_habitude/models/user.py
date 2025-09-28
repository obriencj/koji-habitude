"""
koji-habitude - models.user

User model for koji user objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""


from dataclasses import dataclass
from typing import ClassVar, List, Optional, Any

from koji import MultiCallSession, VirtualCall, ClientSession
from pydantic import Field

from .base import BaseKojiObject, BaseKey
from .change import Change, ChangeReport


@dataclass
class UserCreate(Change):
    name: str
    enabled: Optional[bool]

    def impl_apply(self, session: MultiCallSession):
        return session.createUser(self.name, status=self.enabled)

    def explain(self) -> str:
        status_info = f" (enabled={self.enabled})" if self.enabled is not None else ""
        return f"Create user '{self.name}'{status_info}"


@dataclass
class UserEnable(Change):
    name: str

    def impl_apply(self, session: MultiCallSession):
        return session.enableUser(self.name)

    def explain(self) -> str:
        return f"Enable user '{self.name}'"


@dataclass
class UserDisable(Change):
    name: str

    def impl_apply(self, session: MultiCallSession):
        return session.disableUser(self.name)

    def explain(self) -> str:
        return f"Disable user '{self.name}'"


@dataclass
class UserGrantPermission(Change):
    name: str
    permission: str

    def impl_apply(self, session: MultiCallSession):
        return session.grantPermission(self.name, self.permission, create=True)

    def explain(self) -> str:
        return f"Grant permission '{self.permission}' to user '{self.name}'"


@dataclass
class UserRevokePermission(Change):
    name: str
    permission: str

    def impl_apply(self, session: MultiCallSession):
        return session.revokePermission(self.name, self.permission)

    def explain(self) -> str:
        return f"Revoke permission '{self.permission}' from user '{self.name}'"


@dataclass
class UserAddToGroup(Change):
    name: str
    group: str

    def impl_apply(self, session: MultiCallSession):
        return session.addGroupMember(self.group, self.name, strict=False)

    def explain(self) -> str:
        return f"Add user '{self.name}' to group '{self.group}'"


@dataclass
class UserRemoveFromGroup(Change):
    name: str
    group: str

    def impl_apply(self, session: MultiCallSession):
        return session.dropGroupMember(self.group, self.name)

    def explain(self) -> str:
        return f"Remove user '{self.name}' from group '{self.group}'"


class UserChangeReport(ChangeReport):
    """
    Change report for user objects.
    """

    def create_user(self):
        self.add(UserCreate(self.obj.name, self.obj.enabled))

    def enable_user(self):
        self.add(UserEnable(self.obj.name))

    def disable_user(self):
        self.add(UserDisable(self.obj.name))

    def grant_permission(self, permission: str):
        self.add(UserGrantPermission(self.obj.name, permission))

    def revoke_permission(self, permission: str):
        self.add(UserRevokePermission(self.obj.name, permission))

    def add_to_group(self, group: str):
        self.add(UserAddToGroup(self.obj.name, group))

    def remove_from_group(self, group: str):
        self.add(UserRemoveFromGroup(self.obj.name, group))


    def impl_read(self, session: MultiCallSession):
        self._userinfo: VirtualCall = self.obj.query_exists(session)
        self._permissions: VirtualCall = session.getUserPerms(self.obj.name)


    def impl_compare(self):
        info = self._userinfo.result
        if not info:
            self.create_user()
            for permission in self.obj.permissions:
                self.grant_permission(permission)
            for group in self.obj.groups:
                self.add_to_group(group)
            return

        if self.obj.enabled is not None:
            if info['status'] != self.obj.enabled:
                if self.obj.enabled:
                    self.enable_user()
                else:
                    self.disable_user()

        groups = info['groups']
        for group in self.obj.groups:
            if group not in groups:
                self.add_to_group(group)

        if self.obj.exact_groups:
            for group in groups:
                if group not in self.obj.groups:
                    self.remove_from_group(group)

        perms = self._permissions.result
        for perm in self.obj.permissions:
            if perm not in perms:
                self.grant_permission(perm)

        if self.obj.exact_permissions:
            for perm in perms:
                if perm not in self.obj.permissions:
                    self.revoke_permission(perm)


class User(BaseKojiObject):
    """
    Koji user object model.
    """

    typename: ClassVar[str] = "user"
    _can_split: ClassVar[bool] = True

    groups: List[str] = Field(alias='groups', default_factory=list)
    exact_groups: bool = Field(validation_alias='exact-groups', default=False)

    permissions: List[str] = Field(alias='permissions', default_factory=list)
    exact_permissions: bool = Field(alias='exact-permissions', default=False)

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


    def change_report(self) -> UserChangeReport:
        return UserChangeReport(self)


    @classmethod
    def check_exists(cls, session: ClientSession, key: BaseKey) -> Any:
        return session.getUser(key[1], strict=False, groups=True)


# The end.

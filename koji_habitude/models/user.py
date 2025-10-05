"""
koji-habitude - models.user

User model for koji user objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Assisted, Mostly Human


from dataclasses import dataclass
from typing import ClassVar, List, Optional, Any, TYPE_CHECKING

from koji import MultiCallSession, VirtualCall, ClientSession
from pydantic import Field

from .base import BaseKey, BaseObject
from .change import Change, ChangeReport

if TYPE_CHECKING:
    from ..resolver import Resolver


@dataclass
class UserCreate(Change):
    name: str
    enabled: Optional[bool]

    def impl_apply(self, session: MultiCallSession):
        if self.enabled is None:
            status = 0
        else:
            status = 0 if self.enabled else 1
        return session.createUser(self.name, status=status)

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

    _skippable: ClassVar[bool] = True

    def skip_check_impl(self, resolver: 'Resolver') -> bool:
        perm = resolver.resolve(('permission', self.permission))
        return perm.missing() and not perm.exists()

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

    def impl_read(self, session: MultiCallSession):
        self._userinfo: VirtualCall = self.obj.query_exists(session)
        self._permissions: VirtualCall = session.getUserPerms(self.obj.name)


    def impl_compare(self):
        info = self._userinfo.result
        if not info:
            if not self.obj.was_split():
                # we don't exist, and we didn't split our create to an earlier
                # call, so create now.
                yield UserCreate(self.obj.name, self.obj.enabled)

            for permission in self.obj.permissions:
                yield UserGrantPermission(self.obj.name, permission)
            for group in self.obj.groups:
                yield UserAddToGroup(self.obj.name, group)
            return

        if self.obj.enabled is not None:
            if info['status'] != (0 if self.obj.enabled else 1):
                if self.obj.enabled:
                    yield UserEnable(self.obj.name)
                else:
                    yield UserDisable(self.obj.name)

        groups = info['groups']
        for group in self.obj.groups:
            if group not in groups:
                yield UserAddToGroup(self.obj.name, group)

        if self.obj.exact_groups:
            for group in groups:
                if group not in self.obj.groups:
                    yield UserRemoveFromGroup(self.obj.name, group)

        perms = self._permissions.result
        for perm in self.obj.permissions:
            if perm not in perms:
                yield UserGrantPermission(self.obj.name, perm)

        if self.obj.exact_permissions:
            for perm in perms:
                if perm not in self.obj.permissions:
                    yield UserRevokePermission(self.obj.name, perm)


class User(BaseObject):
    """
    Koji user object model.
    """

    typename: ClassVar[str] = "user"

    groups: List[str] = Field(alias='groups', default_factory=list)
    exact_groups: bool = Field(validation_alias='exact-groups', default=False)

    permissions: List[str] = Field(alias='permissions', default_factory=list)
    exact_permissions: bool = Field(alias='exact-permissions', default=False)

    enabled: Optional[bool] = Field(alias='enabled', default=None)

    _auto_split: ClassVar[bool] = True


    def split(self) -> 'User':
        self._was_split = True
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


    def change_report(self, resolver: 'Resolver') -> UserChangeReport:
        return UserChangeReport(self, resolver)


    @classmethod
    def check_exists(cls, session: ClientSession, key: BaseKey) -> Any:
        return session.getUser(key[1], strict=False, groups=True)


# The end.

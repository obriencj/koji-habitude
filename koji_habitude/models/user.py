"""
koji-habitude - models.user

User model for koji user objects.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Assisted, Mostly Human


from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, Dict, List, Optional

from koji import MultiCallSession, VirtualCall

from ..koji import call_processor, promise_call, VirtualPromise
from .base import BaseKey, CoreModel, CoreObject, RemoteObject
from .change import Add, ChangeReport, Create, Remove, Update
from .compat import Field

if TYPE_CHECKING:
    from ..resolver import Resolver


@dataclass
class UserCreate(Create):
    obj: 'User'

    def impl_apply(self, session: MultiCallSession):
        if self.obj.enabled is None:
            status = 0
        else:
            status = 0 if self.obj.enabled else 1
        return session.createUser(self.obj.name, status=status)

    def summary(self) -> str:
        status_info = f" (enabled={self.obj.enabled})" if self.obj.enabled is not None else ""
        return f"Create user {self.obj.name}{status_info}"


@dataclass
class UserEnable(Update):
    obj: 'User'

    def impl_apply(self, session: MultiCallSession):
        return session.enableUser(self.obj.name)

    def summary(self) -> str:
        return "Enable user"


@dataclass
class UserDisable(Update):
    obj: 'User'

    def impl_apply(self, session: MultiCallSession):
        return session.disableUser(self.obj.name)

    def summary(self) -> str:
        return "Disable user"


@dataclass
class UserGrantPermission(Add):
    obj: 'User'
    permission: str

    _skippable: ClassVar[bool] = True

    def skip_check_impl(self, resolver: 'Resolver') -> bool:
        perm = resolver.resolve(('permission', self.permission))
        return perm.is_phantom()

    def impl_apply(self, session: MultiCallSession):
        return session.grantPermission(self.obj.name, self.permission, create=True)

    def summary(self) -> str:
        return f"Grant permission '{self.permission}'"


@dataclass
class UserRevokePermission(Remove):
    obj: 'User'
    permission: str

    def impl_apply(self, session: MultiCallSession):
        return session.revokePermission(self.obj.name, self.permission)

    def summary(self) -> str:
        return f"Revoke permission '{self.permission}'"


@dataclass
class UserAddToGroup(Add):
    obj: 'User'
    group: str

    _skippable: ClassVar[bool] = True

    def skip_check_impl(self, resolver: 'Resolver') -> bool:
        group = resolver.resolve(('group', self.group))
        return group.is_phantom()

    def impl_apply(self, session: MultiCallSession):
        return session.addGroupMember(self.group, self.obj.name, strict=False)

    def summary(self) -> str:
        return f"Add group '{self.group}'"


@dataclass
class UserRemoveFromGroup(Remove):
    obj: 'User'
    group: str

    def impl_apply(self, session: MultiCallSession):
        return session.dropGroupMember(self.group, self.obj.name)

    def summary(self) -> str:
        return f"Remove group '{self.group}'"


class UserChangeReport(ChangeReport):
    """
    Change report for user objects.
    """

    def impl_compare(self):
        remote = self.obj.remote()
        if not remote:
            if not self.obj.was_split():
                # we don't exist, and we didn't split our create to an earlier
                # call, so create now.
                yield UserCreate(self.obj)

            if self.obj.is_split():
                return

            for permission in self.obj.permissions:
                yield UserGrantPermission(self.obj, permission)
            for group in self.obj.groups:
                yield UserAddToGroup(self.obj, group)
            return

        if self.obj.is_split():
            return

        if self.obj.enabled is not None:
            if remote.enabled != self.obj.enabled:
                if self.obj.enabled:
                    yield UserEnable(self.obj)
                else:
                    yield UserDisable(self.obj)

        groups = remote.groups
        for group in self.obj.groups:
            if group not in groups:
                yield UserAddToGroup(self.obj, group)

        if self.obj.exact_groups:
            for group in groups:
                if group not in self.obj.groups:
                    yield UserRemoveFromGroup(self.obj, group)

        perms = remote.permissions
        for perm in self.obj.permissions:
            if perm not in perms:
                yield UserGrantPermission(self.obj, perm)

        if self.obj.exact_permissions:
            for perm in perms:
                if perm not in self.obj.permissions:
                    yield UserRevokePermission(self.obj, perm)


class UserModel(CoreModel):
    """Field definitions for User objects"""

    typename: ClassVar[str] = "user"

    enabled: Optional[bool] = Field(alias='enabled', default=None)
    groups: List[str] = Field(alias='groups', default_factory=list)
    permissions: List[str] = Field(alias='permissions', default_factory=list)


    def dependency_keys(self) -> List[BaseKey]:
        """
        Users can depend on:
        - Groups
        - Permissions
        """

        deps: List[BaseKey] = []
        deps.extend(('group', group) for group in self.groups)
        deps.extend(('permission', permission) for permission in self.permissions)
        return deps


    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        data = super().model_dump(**kwargs)
        data['groups'] = sorted(data['groups'])
        data['permissions'] = sorted(data['permissions'])
        return data


class User(UserModel, CoreObject):
    """
    Local user object from YAML.
    """

    exact_groups: bool = Field(validation_alias='exact-groups', default=False)
    exact_permissions: bool = Field(alias='exact-permissions', default=False)

    _auto_split: ClassVar[bool] = True


    def split(self) -> 'User':
        child = User(name=self.name, enabled=self.enabled)
        child._is_split = True
        self._was_split = True
        return child


    def change_report(self, resolver: 'Resolver') -> UserChangeReport:
        return UserChangeReport(self, resolver)


    @classmethod
    def query_remote(cls, session: MultiCallSession, key: BaseKey) -> 'VirtualCall[RemoteUser]':
        return call_processor(RemoteUser.from_koji, session.getUser, key[1], strict=False, groups=True)


class RemoteUser(UserModel, RemoteObject):
    """
    Remote user object from Koji API
    """

    @classmethod
    def from_koji(cls, data: Optional[Dict[str, Any]]):
        if data is None:
            return None

        return cls(
            koji_id=data['id'],
            name=data['name'],
            groups=data['groups'],
            enabled=(data['status'] == 0))


    def set_koji_perms(self, perms: VirtualPromise):
        self.permissions = list(perms.result)


    def load_additional_data(self, session: MultiCallSession):
        promise_call(self.set_koji_perms, session.getUserPerms, self.name)


# The end.

"""
koji-habitude - models.group

Group model for koji group objects.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated with Human Rework


from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, Dict, List, Optional

from koji import MultiCallSession, VirtualCall

from ..koji import call_processor, promise_call
from .base import BaseKey, CoreModel, CoreObject, RemoteObject
from .change import Add, ChangeReport, Create, Remove, Update
from .compat import Field

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

    def impl_compare(self):
        remote = self.obj.remote()
        if not remote:
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

        if remote.enabled != self.obj.enabled:
            if self.obj.enabled:
                yield GroupEnable(self.obj)
            else:
                yield GroupDisable(self.obj)

        members = remote.members
        for member in self.obj.members:
            if member not in members:
                yield GroupAddMember(self.obj, member)

        if self.obj.exact_members:
            for member in members:
                if member not in self.obj.members:
                    yield GroupRemoveMember(self.obj, member)

        permissions = remote.permissions
        for permission in self.obj.permissions:
            if permission not in permissions:
                yield GroupAddPermission(self.obj, permission)

        if self.obj.exact_permissions:
            for permission in permissions:
                if permission not in self.obj.permissions:
                    yield GroupRemovePermission(self.obj, permission)


class GroupModel(CoreModel):
    """
    Field definitions for Group objects
    """

    typename: ClassVar[str] = "group"

    enabled: bool = Field(alias='enabled', default=True)
    members: List[str] = Field(alias='members', default_factory=list)
    permissions: List[str] = Field(alias='permissions', default_factory=list)


    def dependency_keys(self) -> List[BaseKey]:
        deps: List[BaseKey] = []
        deps.extend([('user', member) for member in self.members])
        deps.extend([('permission', permission) for permission in self.permissions])
        return deps


    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        data = super().model_dump(**kwargs)
        data['members'] = sorted(data['members'])
        data['permissions'] = sorted(data['permissions'])
        return data


class Group(GroupModel, CoreObject):
    """
    Local group object from YAML.
    """

    exact_members: bool = Field(alias='exact-members', default=False)
    exact_permissions: bool = Field(alias='exact-permissions', default=False)

    _auto_split: ClassVar[bool] = True


    def change_report(self, resolver: 'Resolver') -> GroupChangeReport:
        return GroupChangeReport(self, resolver)


    @classmethod
    def query_remote(cls, session: MultiCallSession, key: BaseKey) -> 'VirtualCall[RemoteGroup]':
        return call_processor(RemoteGroup.from_koji, session.getUser, key[1], strict=False)


class RemoteGroup(GroupModel, RemoteObject):
    """
    Remote group object from Koji API
    """

    @classmethod
    def from_koji(cls, data: Optional[Dict[str, Any]]):
        if data is None:
            return None

        return cls(
            koji_id=data['id'],
            name=data['name'],
            enabled=(data.get('status', 0) == 0),
        )


    def set_koji_members(self, result):
        self.members = [m['name'] for m in result.result]


    def set_koji_permissions(self, result):
        self.permissions = list(result.result)


    def load_additional_data(self, session: MultiCallSession):
        promise_call(self.set_koji_members, session.getGroupMembers, self.name)
        promise_call(self.set_koji_permissions, session.getUserPerms, self.name)


# The end.

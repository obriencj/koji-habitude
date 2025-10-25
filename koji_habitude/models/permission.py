"""
koji-habitude - models.permission

Permission model for koji permission objects.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated with Human Rework


import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Optional

from koji import MultiCallSession, VirtualCall

from ..koji import call_processor
from .base import BaseKey, CoreModel, CoreObject, RemoteObject
from .change import ChangeReport, Create, Update
from .compat import Field

if TYPE_CHECKING:
    from ..resolver import Resolver


logger = logging.getLogger(__name__)


@dataclass
class PermissionCreate(Create):
    obj: 'Permission'

    def impl_apply(self, session: MultiCallSession):
        currentuser = vars(session)['_currentuser']['id']
        # there's no way to create a permission on its own, you have to grant it to someone
        # and then revoke it. We record the logged in user as _currentuser when we use the
        # `koji_habituse.koji.session` call.
        res = session.grantPermission(
            currentuser, self.obj.name, create=True,
            description=self.obj.description)
        session.revokePermission(currentuser, self.obj.name)
        return res

    def summary(self) -> str:
        desc_info = f" with description {self.obj.description!r}" if self.obj.description else ""
        return f"Create permission {self.obj.name}{desc_info}"


@dataclass
class PermissionSetDescription(Update):
    obj: 'Permission'
    description: str

    def impl_apply(self, session: MultiCallSession):
        return session.editPermission(self.obj.name, description=self.description)

    def summary(self) -> str:
        if self.description:
            return f"Set description to {self.description!r}"
        else:
            return "Clear description"


class PermissionChangeReport(ChangeReport):
    """
    Change report for permission objects.
    """

    def impl_compare(self):
        remote = self.obj.remote()
        if not remote:
            yield PermissionCreate(self.obj)
            return

        if remote.description != self.obj.description:
            yield PermissionSetDescription(self.obj, self.obj.description)


class PermissionModel(CoreModel):
    """Field definitions for Permission objects"""

    typename: ClassVar[str] = "permission"

    description: Optional[str] = Field(alias='description', default=None)


class Permission(PermissionModel, CoreObject):
    """
    Local permission object from YAML.
    """

    def change_report(self, resolver: 'Resolver') -> PermissionChangeReport:
        return PermissionChangeReport(self, resolver)


    @classmethod
    def query_remote(cls, session: MultiCallSession, key: BaseKey) -> 'VirtualCall[RemotePermission]':
        name = key[1]

        def filter_for_perm(perms):
            for perm in perms:
                if perm['name'] == name:
                    return RemotePermission.from_koji(perm)
            return None

        return call_processor(filter_for_perm, session.getAllPerms)


class RemotePermission(PermissionModel, RemoteObject):
    """Remote permission object from Koji API"""

    @classmethod
    def from_koji(cls, data: Optional[Dict[str, Any]]):
        if data is None:
            return None

        return cls(
            koji_id=data['id'],
            name=data['name'],
            description=data.get('description')
        )


# The end.

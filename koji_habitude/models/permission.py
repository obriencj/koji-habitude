"""
koji-habitude - models.permission

Permission model for koji permission objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""


from dataclasses import dataclass
from functools import partial
import logging
from typing import ClassVar, Optional, Any

from koji import MultiCallSession, VirtualCall, ClientSession
from pydantic import Field

from .base import BaseKojiObject, BaseKey
from .change import Change, ChangeReport
from ..koji import call_processor


logger = logging.getLogger(__name__)


def getPermission(session: ClientSession, name: str):

    def filter_for_perm(perms):
        logger.debug(f"Filtering for permission: {name}")
        for perm in perms:
            if perm['name'] == name:
                return perm
        return None

    return call_processor(filter_for_perm, session.getAllPerms)


@dataclass
class PermissionCreate(Change):
    name: str
    description: Optional[str]

    def impl_apply(self, session: MultiCallSession):
        currentuser = vars(session)['_currentuser']['id']
        # there's no way to create a permission on its own, you have to grant it to someone
        # and then revoke it. We record the logged in user as _currentuser when we use the
        # `koji_habituse.koji.session` call.
        res = session.grantPermission(
            currentuser, self.name, create=True,
            description=self.description)
        session.revokePermission(currentuser, self.name)
        return res

    def explain(self) -> str:
        desc_info = f" with description '{self.description}'" if self.description else ""
        return f"Create permission '{self.name}'{desc_info}"


@dataclass
class PermissionSetDescription(Change):
    name: str
    description: str

    def impl_apply(self, session: MultiCallSession):
        return session.editPermission(self.name, description=self.description)

    def explain(self) -> str:
        return f"Set description for permission '{self.name}' to '{self.description}'"


class PermissionChangeReport(ChangeReport):
    """
    Change report for permission objects.
    """

    def create_permission(self):
        self.add(PermissionCreate(self.obj.name, self.obj.description))

    def set_description(self):
        self.add(PermissionSetDescription(self.obj.name, self.obj.description))

    def impl_read(self, session: MultiCallSession):
        self._permissioninfo: VirtualCall = self.obj.query_exists(session)


    def impl_compare(self):
        info = self._permissioninfo.result
        if not info:
            self.create_permission()
            return

        if info['description'] != self.obj.description:
            self.set_description()


class Permission(BaseKojiObject):
    """
    Koji permission object model.
    """

    typename: ClassVar[str] = "permission"

    description: Optional[str] = Field(alias='description', default=None)


    def change_report(self) -> PermissionChangeReport:
        return PermissionChangeReport(self)


    @classmethod
    def check_exists(cls, session: ClientSession, key: BaseKey) -> Any:
        # XXX TODO: NOT WORKING
        return getPermission(session, key[1])


# The end.

"""
koji-habitude - models.permission

Permission model for koji permission objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""


from dataclasses import dataclass
from typing import ClassVar, Optional

from koji import MultiCallSession, VirtualCall
from pydantic import Field

from .base import BaseKojiObject
from .change import Change, ChangeReport


@dataclass
class PermissionCreate(Change):
    name: str
    description: Optional[str]

    def impl_apply(self, session: MultiCallSession):
        currentuser = vars(session)['_currentuser']['id']
        # there's no way to create a permission on its own, you have to grant it to someone
        # and then revoke it. We record the logged in user as _currentuser when we use the
        # `koji_habituse.koji.session` call.
        res = session.grantPermission(currentuser, self.name, description=self.description)
        session.revokePermission(currentuser, self.name)
        return res


@dataclass
class PermissionSetDescription(Change):
    name: str
    description: str

    def impl_apply(self, session: MultiCallSession):
        return session.editPermission(self.name, description=self.description)


class PermissionChangeReport(ChangeReport):
    """
    Change report for permission objects.
    """


    def create_permission(self):
        self.add(PermissionCreate(self.obj.name, self.obj.description))


    def set_description(self):
        self.add(PermissionSetDescription(self.obj.name, self.obj.description))


    def impl_read(self, session: MultiCallSession):
        self._permissioninfo: VirtualCall = session.getPermission(self.obj.name)


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


# The end.

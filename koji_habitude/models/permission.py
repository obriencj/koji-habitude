"""
koji-habitude - models.permission

Permission model for koji permission objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated with Human Rework


from dataclasses import dataclass
from functools import partial
import logging
from typing import ClassVar, Optional, Any, TYPE_CHECKING

from koji import MultiCallSession, VirtualCall, ClientSession
from pydantic import Field

from .base import BaseObject, BaseKey
from .change import Change, ChangeReport, Create, Update
from ..koji import call_processor

if TYPE_CHECKING:
    from ..resolver import Resolver


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
        return f"Create permission '{self.obj.name}'{desc_info}"


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

    def impl_read(self, session: MultiCallSession):
        self._permissioninfo: VirtualCall = self.obj.query_exists(session)


    def impl_compare(self):
        info = self._permissioninfo.result
        if not info:
            yield PermissionCreate(self.obj)
            return

        if info['description'] != self.obj.description:
            yield PermissionSetDescription(self.obj, self.obj.description)


class Permission(BaseObject):
    """
    Koji permission object model.
    """

    typename: ClassVar[str] = "permission"

    description: Optional[str] = Field(alias='description', default=None)


    def change_report(self, resolver: 'Resolver') -> PermissionChangeReport:
        return PermissionChangeReport(self, resolver)


    @classmethod
    def check_exists(cls, session: ClientSession, key: BaseKey) -> Any:
        return getPermission(session, key[1])


# The end.

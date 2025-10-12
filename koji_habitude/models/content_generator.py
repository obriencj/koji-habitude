"""
koji-habitude - models.content_generator

Content generator model for koji content generator objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 4.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Assisted, Mostly Human


from dataclasses import dataclass
from typing import Any, ClassVar, List, Sequence, TYPE_CHECKING

from pydantic import Field

from koji import MultiCallSession, VirtualCall, ClientSession

from .base import BaseKey, BaseObject
from .change import ChangeReport, Create, Add, Remove
from ..koji import call_processor

if TYPE_CHECKING:
    from ..resolver import Resolver


def getContentGenerator(session: ClientSession, name: str):

    def filter_for_cg(cglist):
        dat = cglist.get(name)
        if dat is not None:
            dat['name'] = name
        return None

    return call_processor(filter_for_cg, session.listCGs)


@dataclass
class ContentGeneratorCreate(Create):
    obj: 'ContentGenerator'

    def impl_apply(self, session: MultiCallSession):
        currentuser = vars(session)['_currentuser']['id']
        # similar to permissions, there is no way to create a CG on its own, it
        # can only be created as a side-effect of granting it someone. So we'll
        # give it to ourselves and then revoke it.
        res = session.grantCGAccess(currentuser, self.obj.name, create=True)
        session.revokeCGAccess(currentuser, self.obj.name)
        return res

    def summary(self) -> str:
        return f"Create content generator {self.obj.name}"


@dataclass
class ContentGeneratorAddUser(Add):
    obj: 'ContentGenerator'
    user: str

    def impl_apply(self, session: MultiCallSession):
        return session.grantCGAccess(self.user, self.obj.name)

    def summary(self) -> str:
        return f"Grant cg-import for user {self.user}"


@dataclass
class ContentGeneratorRemoveUser(Remove):
    obj: 'ContentGenerator'
    user: str

    def impl_apply(self, session: MultiCallSession):
        return session.revokeCGAccess(self.user, self.obj.name)

    def summary(self) -> str:
        return f"Revoke cg-import from user {self.user}"


class ContentGeneratorChangeReport(ChangeReport):
    """
    Change report for content generator objects.
    """

    def impl_read(self, session: MultiCallSession):
        self._cg_info: VirtualCall = self.obj.query_exists(session)


    def impl_compare(self):
        info = self._cg_info.result
        if not info:
            yield ContentGeneratorCreate(self.obj)
            for user in self.obj.users:
                yield ContentGeneratorAddUser(self.obj, user)
            return

        users = info['users']
        for user in self.obj.users:
            if user not in users:
                yield ContentGeneratorAddUser(self.obj, user)

        if self.obj.exact_users:
            for user in users:
                if user not in self.obj.users:
                    yield ContentGeneratorRemoveUser(self.obj, user)


class ContentGenerator(BaseObject):
    """
    Koji content generator object model.
    """

    typename: ClassVar[str] = "content-generator"

    users: List[str] = Field(alias='users', default_factory=list)
    exact_users: bool = Field(alias='exact-users', default=False)


    def dependency_keys(self) -> Sequence[BaseKey]:
        return [('user', user) for user in self.users]


    def change_report(self, resolver: 'Resolver') -> ContentGeneratorChangeReport:
        return ContentGeneratorChangeReport(self, resolver)


    @classmethod
    def check_exists(cls, session: ClientSession, key: BaseKey) -> Any:
        return getContentGenerator(session, key[1])


# The end.

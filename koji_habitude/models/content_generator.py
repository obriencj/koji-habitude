"""
koji-habitude - models.content_generator

Content generator model for koji content generator objects.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 4.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Assisted, Mostly Human


from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, Dict, List, Optional, Sequence

from koji import MultiCallSession, VirtualCall

from ..koji import call_processor
from .base import BaseKey, CoreModel, CoreObject, RemoteObject
from .change import Add, ChangeReport, Create, Remove
from .compat import Field

if TYPE_CHECKING:
    from ..resolver import Resolver


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

    def impl_compare(self):
        remote = self.obj.remote()
        if not remote:
            yield ContentGeneratorCreate(self.obj)
            for user in self.obj.users:
                yield ContentGeneratorAddUser(self.obj, user)
            return

        users = remote.users
        for user in self.obj.users:
            if user not in users:
                yield ContentGeneratorAddUser(self.obj, user)

        if self.obj.exact_users:
            for user in users:
                if user not in self.obj.users:
                    yield ContentGeneratorRemoveUser(self.obj, user)


class ContentGeneratorModel(CoreModel):
    """
    Field definitions for ContentGenerator objects
    """

    typename: ClassVar[str] = "content-generator"

    users: List[str] = Field(alias='users', default_factory=list)
    exact_users: bool = Field(alias='exact-users', default=False)


    def dependency_keys(self) -> Sequence[BaseKey]:
        return [('user', user) for user in self.users]


class ContentGenerator(ContentGeneratorModel, CoreObject):
    """
    Local content generator object from YAML.
    """

    def change_report(self, resolver: 'Resolver') -> ContentGeneratorChangeReport:
        return ContentGeneratorChangeReport(self, resolver)


    @classmethod
    def query_remote(cls, session: MultiCallSession, key: BaseKey) -> 'VirtualCall[RemoteContentGenerator]':
        name = key[1]

        def filter_for_cg(cglist):
            dat = cglist.get(name)
            if dat is not None:
                dat['name'] = name
                return RemoteContentGenerator.from_koji(dat)
            return None

        return call_processor(filter_for_cg, session.listCGs)


class RemoteContentGenerator(ContentGeneratorModel, RemoteObject):
    """
    Remote content generator object from Koji API
    """

    @classmethod
    def from_koji(cls, data: Optional[Dict[str, Any]]):
        if data is None:
            return None

        return cls(
            koji_id=data['id'],
            name=data['name'],
            users=data.get('users', []),
            exact_users=False  # Default for remote objects
        )


# The end.

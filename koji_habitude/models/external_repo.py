"""
koji-habitude - models.external_repo

External repository model for koji external repo objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated with Human Rework


from dataclasses import dataclass
from typing import ClassVar, Any, TYPE_CHECKING

from koji import ClientSession, MultiCallSession, VirtualCall
from pydantic import Field

from .base import BaseObject, BaseKey
from .change import ChangeReport, Change

if TYPE_CHECKING:
    from ..resolver import Resolver


@dataclass
class ExternalRepoCreate(Change):
    name: str
    url: str

    def impl_apply(self, session: MultiCallSession):
        return session.createExternalRepo(self.name, self.url)

    def explain(self) -> str:
        return f"Create external repo '{self.name}' with URL '{self.url}'"


@dataclass
class ExternalRepoSetURL(Change):
    name: str
    url: str

    def impl_apply(self, session: MultiCallSession):
        return session.editExternalRepo(self.name, url=self.url)

    def explain(self) -> str:
        return f"Set URL for external repo '{self.name}' to '{self.url}'"


class ExternalRepoChangeReport(ChangeReport):

    def impl_read(self, session: MultiCallSession):
        self._external_repoinfo: VirtualCall = self.obj.query_exists(session)


    def impl_compare(self):
        info = self._external_repoinfo.result
        if not info:
            yield ExternalRepoCreate(self.obj.name, self.obj.url)
            return

        if info['url'] != self.obj.url:
            yield ExternalRepoSetURL(self.obj.name, self.obj.url)


class ExternalRepo(BaseObject):
    """
    Koji external repository object model.
    """

    typename: ClassVar[str] = "external-repo"

    url: str = Field(alias='url', pattern=r'^https?://')


    def change_report(self, resolver: 'Resolver') -> ExternalRepoChangeReport:
        return ExternalRepoChangeReport(self, resolver)


    @classmethod
    def check_exists(cls, session: ClientSession, key: BaseKey) -> Any:
        return session.getExternalRepo(key[1], strict=False)


# The end.

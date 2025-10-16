"""
koji-habitude - models.external_repo

External repository model for koji external repo objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated with Human Rework


from dataclasses import dataclass
from re import match
from typing import TYPE_CHECKING, ClassVar

from koji import MultiCallSession, VirtualCall

from .base import BaseKey, BaseObject
from .change import ChangeReport, Create, Update
from .compat import Field, field_validator

if TYPE_CHECKING:
    from ..resolver import Resolver


@dataclass
class ExternalRepoCreate(Create):
    obj: 'ExternalRepo'

    def impl_apply(self, session: MultiCallSession):
        return session.createExternalRepo(self.obj.name, self.obj.url)

    def summary(self) -> str:
        return f"Create external repo {self.obj.name} with URL {self.obj.url}"


@dataclass
class ExternalRepoSetURL(Update):
    obj: 'ExternalRepo'
    url: str

    def impl_apply(self, session: MultiCallSession):
        return session.editExternalRepo(self.obj.name, url=self.url)

    def summary(self) -> str:
        return f"Set URL to {self.url}"


class ExternalRepoChangeReport(ChangeReport):

    def impl_read(self, session: MultiCallSession):
        self._external_repoinfo: VirtualCall = self.obj.query_exists(session)


    def impl_compare(self):
        info = self._external_repoinfo.result
        if not info:
            yield ExternalRepoCreate(self.obj)
            return

        if info['url'] != self.obj.url:
            yield ExternalRepoSetURL(self.obj, self.obj.url)


class ExternalRepo(BaseObject):
    """
    Koji external repository object model.
    """

    typename: ClassVar[str] = "external-repo"

    url: str = Field(alias='url')


    @field_validator('url', mode='before')
    def validate_url(cls, v):
        if not match(r'^https?://', v):
            raise ValueError("url must start with http or https")
        return v


    def change_report(self, resolver: 'Resolver') -> ExternalRepoChangeReport:
        return ExternalRepoChangeReport(self, resolver)


    @classmethod
    def check_exists(cls, session: MultiCallSession, key: BaseKey) -> VirtualCall:
        return session.getExternalRepo(key[1], strict=False)


# The end.

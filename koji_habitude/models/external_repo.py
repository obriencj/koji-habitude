"""
koji-habitude - models.external_repo

External repository model for koji external repo objects.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated with Human Rework


from dataclasses import dataclass
from re import match
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Optional

from koji import MultiCallSession, VirtualCall

from ..koji import call_processor
from .base import BaseKey, CoreModel, CoreObject, RemoteObject
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

    def impl_compare(self):
        remote = self.obj.remote()
        if not remote:
            yield ExternalRepoCreate(self.obj)
            return

        if remote.url != self.obj.url:
            yield ExternalRepoSetURL(self.obj, self.obj.url)


class ExternalRepoModel(CoreModel):
    """
    Field definitions for ExternalRepo objects
    """

    typename: ClassVar[str] = "external-repo"

    url: str = Field(alias='url')


class ExternalRepo(ExternalRepoModel, CoreObject):
    """
    Local external repository object from YAML.
    """

    @field_validator('url', mode='before')
    def validate_url(cls, v):
        if not match(r'^https?://', v):
            raise ValueError("url must start with http or https")
        return v


    def change_report(self, resolver: 'Resolver') -> ExternalRepoChangeReport:
        return ExternalRepoChangeReport(self, resolver)


    @classmethod
    def query_remote(cls, session: MultiCallSession, key: BaseKey) -> 'VirtualCall[RemoteExternalRepo]':
        return call_processor(
            RemoteExternalRepo.from_koji,
            session.getExternalRepo, key[1], strict=False)


class RemoteExternalRepo(ExternalRepoModel, RemoteObject):
    """
    Remote external repository object from Koji API
    """

    @classmethod
    def from_koji(cls, data: Optional[Dict[str, Any]]):
        if data is None:
            return None

        return cls(
            koji_id=data['id'],
            name=data['name'],
            url=data['url']
        )


# The end.

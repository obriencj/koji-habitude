"""
koji-habitude - models.external_repo

External repository model for koji external repo objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""


from dataclasses import dataclass
from typing import ClassVar

from koji import MultiCallSession, VirtualCall
from pydantic import Field

from .base import BaseKojiObject
from .change import ChangeReport, Change


@dataclass
class ExternalRepoCreate(Change):
    name: str
    url: str

    def impl_apply(self, session: MultiCallSession):
        return session.createExternalRepo(self.name, self.url)


@dataclass
class ExternalRepoSetURL(Change):
    name: str
    url: str

    def impl_apply(self, session: MultiCallSession):
        return session.editExternalRepo(self.name, url=self.url)


class ExternalRepoChangeReport(ChangeReport):

    def create_external_repo(self):
        self.add(ExternalRepoCreate(self.obj.name, self.obj.url))

    def set_url(self):
        self.add(ExternalRepoSetURL(self.obj.name, self.obj.url))


    def impl_read(self, session: MultiCallSession):
        self._external_repoinfo: VirtualCall = session.getExternalRepo(self.obj.name)


    def impl_compare(self):
        info = self._external_repoinfo.result
        if not info:
            self.create_external_repo()
            return

        if info['url'] != self.obj.url:
            self.set_url()


class ExternalRepo(BaseKojiObject):
    """
    Koji external repository object model.
    """

    typename: ClassVar[str] = "external-repo"

    url: str = Field(alias='url', pattern=r'^https?://')

    def change_report(self) -> ExternalRepoChangeReport:
        return ExternalRepoChangeReport(self)


# The end.

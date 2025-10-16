"""
koji-habitude - models.archive_type

Archive type model for koji archive type objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 4.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated with Human Rework


from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, List, Literal

from koji import MultiCallSession, VirtualCall

from ..koji import call_processor
from .base import BaseKey, BaseObject
from .change import ChangeReport, Create
from .compat import Field, field_validator

if TYPE_CHECKING:
    from ..resolver import Resolver


def getArchiveType(session: MultiCallSession, name: str):
    def filter_for_atype(atlist):
        for at in atlist:
            if at['name'] == name:
                return at
        return None

    return call_processor(filter_for_atype, session.getArchiveTypes)


@dataclass
class ArchiveTypeCreate(Create):
    obj: 'ArchiveType'

    def impl_apply(self, session: MultiCallSession):
        return session.addArchiveType(
            name=self.obj.name,
            description=self.obj.description,
            extensions=" ".join(self.obj.extensions),
            compression_type=self.obj.compression)

    def summary(self) -> str:
        return f"Create archive type {self.obj.name}"


class ArchiveTypeChangeReport(ChangeReport):
    """
    Change report for archive type objects.
    """

    def impl_read(self, session: MultiCallSession):
        self._atypeinfo: VirtualCall = self.obj.query_exists(session)


    def impl_compare(self):
        info = self._atypeinfo.result
        if not info:
            yield ArchiveTypeCreate(self.obj)

        # The current implemention of koji doesn't support updating the details
        # of an archive type once it's created. I filed an RFE to enable this, but
        # we'll need to inject a version check if it ever gets implemented.

        # https://pagure.io/koji/issue/4478

        return


class ArchiveType(BaseObject):
    """
    Koji archive type object model.
    """

    typename: ClassVar[str] = "archive-type"

    description: str = Field(alias='description', default='')
    extensions: List[str] = Field(alias='extensions', default=[])
    compression: Literal['tar', 'zip', None] = Field(alias='compression-type', default=None)


    @field_validator('extensions', mode='after')
    def validate_extensions(cls, v):
        for i, ext in enumerate(v):
            if ext.startswith('.'):
                v[i] = ext.lstrip('.')
        return list(set(v))


    def change_report(self, resolver: 'Resolver') -> ArchiveTypeChangeReport:
        return ArchiveTypeChangeReport(self, resolver)


    @classmethod
    def check_exists(cls, session: MultiCallSession, key: BaseKey) -> VirtualCall:
        return getArchiveType(session, key[1])


# The end.

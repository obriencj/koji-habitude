"""
koji-habitude - models.archive_type

Archive type model for koji archive type objects.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 4.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated with Human Rework


from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, Dict, List, Literal, Optional

from koji import MultiCallSession, VirtualCall

from ..koji import call_processor
from .base import BaseKey, CoreModel, CoreObject, RemoteObject
from .change import ChangeReport, Create
from .compat import Field, field_validator

if TYPE_CHECKING:
    from ..resolver import Resolver


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

    def impl_compare(self):
        remote = self.obj.remote()
        if not remote:
            yield ArchiveTypeCreate(self.obj)
            return

        # The current implemention of koji doesn't support updating the details
        # of an archive type once it's created. I filed an RFE to enable this, but
        # we'll need to inject a version check if it ever gets implemented.

        # https://pagure.io/koji/issue/4478

        return


class ArchiveTypeModel(CoreModel):
    """
    Field definitions for ArchiveType objects
    """

    typename: ClassVar[str] = "archive-type"

    name: str = Field(alias='name')
    description: str = Field(alias='description', default='')
    extensions: List[str] = Field(alias='extensions', default=[])
    compression: Literal['tar', 'zip', None] = Field(alias='compression-type', default=None)


    @field_validator('extensions', mode='after')
    def validate_extensions(cls, v):
        for i, ext in enumerate(v):
            if ext.startswith('.'):
                v[i] = ext.lstrip('.')
        return list(set(v))


class ArchiveType(ArchiveTypeModel, CoreObject):
    """
    Local archive type object from YAML.
    """

    def change_report(self, resolver: 'Resolver') -> ArchiveTypeChangeReport:
        return ArchiveTypeChangeReport(self, resolver)


    @classmethod
    def query_remote(cls, session: MultiCallSession, key: BaseKey) -> VirtualCall:
        name = key[1]

        def filter_for_atype(atlist):
            for at in atlist:
                if at['name'] == name:
                    return RemoteArchiveType.from_koji(at)
            return None

        return call_processor(filter_for_atype, session.getArchiveTypes)


class RemoteArchiveType(ArchiveTypeModel, RemoteObject):
    """
    Remote archive type object from Koji API
    """

    @classmethod
    def from_koji(cls, data: Optional[Dict[str, Any]]):
        if data is None:
            return None

        return cls(
            koji_id=data['id'],
            name=data['name'],
            description=data.get('description', ''),
            extensions=data.get('extensions', '').split(),
            compression=data.get('compression_type')
        )


# The end.

"""
koji-habitude - models.build_type

Build type model for koji build type objects.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 4.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated with Human Rework


from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Optional

from koji import MultiCallSession, VirtualCall

from ..koji import call_processor
from .base import BaseKey, CoreModel, CoreObject, RemoteObject
from .change import ChangeReport, Create

if TYPE_CHECKING:
    from ..resolver import Resolver


@dataclass
class BuildTypeCreate(Create):
    obj: 'BuildType'

    def impl_apply(self, session: MultiCallSession):
        return session.addBType(self.obj.name)

    def summary(self) -> str:
        return f"Create build type {self.obj.name}"


class BuildTypeChangeReport(ChangeReport):
    """
    Change report for build type objects.
    """

    def impl_compare(self):
        remote = self.obj.remote()
        if not remote:
            yield BuildTypeCreate(self.obj)


class BuildTypeModel(CoreModel):
    """
    Field definitions for BuildType objects
    """

    typename: ClassVar[str] = "build-type"


class BuildType(BuildTypeModel, CoreObject):
    """
    Local build type object from YAML.
    """

    def change_report(self, resolver: 'Resolver') -> BuildTypeChangeReport:
        return BuildTypeChangeReport(self, resolver)


    @classmethod
    def query_remote(cls, session: MultiCallSession, key: BaseKey) -> 'VirtualCall[RemoteBuildType]':
        name = key[1]

        def filter_for_btype(btlist):
            if btlist:
                return RemoteBuildType.from_koji(btlist[0])
            return None

        return call_processor(filter_for_btype, session.listBTypes, query={'name': name})


class RemoteBuildType(BuildTypeModel, RemoteObject):
    """
    Remote build type object from Koji API
    """

    @classmethod
    def from_koji(cls, data: Optional[Dict[str, Any]]):
        if data is None:
            return None

        return cls(
            koji_id=data['id'],
            name=data['name']
        )


# The end.

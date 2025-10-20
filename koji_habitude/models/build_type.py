"""
koji-habitude - models.build_type

Build type model for koji build type objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 4.5 Sonnet via Cursor
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


def getBuildType(session: MultiCallSession, name: str):
    def filter_for_btype(btlist):
        return btlist[0] if btlist else None

    return call_processor(filter_for_btype, session.listBTypes, query={'name': name})


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

    def impl_read(self, session: MultiCallSession):
        self._btypeinfo: VirtualCall = self.obj.query_exists(session)


    def impl_compare(self):
        info = self._btypeinfo.result
        if not info:
            yield BuildTypeCreate(self.obj)


class BuildTypeModel(CoreModel):
    """Field definitions for BuildType objects"""

    typename: ClassVar[str] = "build-type"


class BuildType(BuildTypeModel, CoreObject):
    """
    Local build type object from YAML.
    """

    def change_report(self, resolver: 'Resolver') -> BuildTypeChangeReport:
        return BuildTypeChangeReport(self, resolver)

    @classmethod
    def query_remote(cls, session: MultiCallSession, key: BaseKey) -> VirtualCall:
        return call_processor(RemoteBuildType.from_koji, session.getBuildType, key[1], strict=False)

    @classmethod
    def check_exists(cls, session: MultiCallSession, key: BaseKey) -> VirtualCall:
        return getBuildType(session, key[1])


class RemoteBuildType(BuildTypeModel, RemoteObject):
    """Remote build type object from Koji API"""

    @classmethod
    def from_koji(cls, data: Optional[Dict[str, Any]]):
        if data is None:
            return None

        return cls(
            name=data['name']
        )

    def load_additional_data(self, session: MultiCallSession):
        # Load additional data if needed
        pass


# The end.

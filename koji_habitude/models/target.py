"""
koji-habitude - models.target

Target model for koji build target objects.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 3.5 Sonnet via Cursor
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Optional, Sequence

from koji import MultiCallSession, VirtualCall

from ..koji import call_processor
from .base import BaseKey, CoreModel, CoreObject, RemoteObject
from .change import ChangeReport, Create, Update
from .compat import Field

if TYPE_CHECKING:
    from ..resolver import Resolver


@dataclass
class TargetCreate(Create):
    obj: 'Target'

    _skippable: ClassVar[bool] = True

    def skip_check_impl(self, resolver: 'Resolver') -> bool:
        build_tag = resolver.resolve(('tag', self.obj.build_tag))
        if build_tag.is_phantom():
            return True

        dest_tag_name = self.obj.dest_tag or self.obj.name
        dest_tag = resolver.resolve(('tag', dest_tag_name))
        if dest_tag.is_phantom():
            return True

        return False

    def impl_apply(self, session: MultiCallSession) -> VirtualCall:
        return session.createBuildTarget(
            self.obj.name, self.obj.build_tag,
            self.obj.dest_tag or self.obj.name)

    def summary(self) -> str:
        dest_tag = self.obj.dest_tag or self.obj.name
        return f"Create target {self.obj.name} with build_tag {self.obj.build_tag} and dest_tag {dest_tag}"


@dataclass
class TargetEdit(Update):
    obj: 'Target'

    _skippable: ClassVar[bool] = True

    def skip_check_impl(self, resolver: 'Resolver') -> bool:
        build_tag = resolver.resolve(('tag', self.obj.build_tag))
        if build_tag.is_phantom():
            return True

        dest_tag_name = self.obj.dest_tag or self.obj.name
        dest_tag = resolver.resolve(('tag', dest_tag_name))
        if dest_tag.is_phantom():
            return True

        return False

    def impl_apply(self, session: MultiCallSession) -> VirtualCall:
        # thank you, koji-typing
        return session.editBuildTarget(
            self.obj.name, self.obj.name,
            self.obj.build_tag, self.obj.dest_tag or self.obj.name)

    def summary(self) -> str:
        dest_tag = self.obj.dest_tag or self.obj.name
        return f"Update build_tag to {self.obj.build_tag} and dest_tag to {dest_tag}"


class TargetChangeReport(ChangeReport):

    def impl_compare(self):
        remote = self.obj.remote()
        if remote is None:
            yield TargetCreate(self.obj)
            return

        build_tag = remote.build_tag
        dest_tag = remote.dest_tag

        if build_tag != self.obj.build_tag or dest_tag != self.obj.dest_tag:
            yield TargetEdit(self.obj)


class TargetModel(CoreModel):
    """
    Field definitions for Target objects
    """

    typename: ClassVar[str] = "target"

    build_tag: str = Field(alias='build-tag')
    dest_tag: Optional[str] = Field(alias='dest-tag', default=None)


    def dependency_keys(self) -> Sequence[BaseKey]:
        return [
            ('tag', self.build_tag),
            ('tag', self.dest_tag or self.name),
        ]


class Target(TargetModel, CoreObject):
    """
    Local target object from YAML.
    """

    def change_report(self, resolver: 'Resolver') -> TargetChangeReport:
        return TargetChangeReport(self, resolver)


    @classmethod
    def query_remote(cls, session: MultiCallSession, key: BaseKey) -> 'VirtualCall[RemoteTarget]':
        return call_processor(RemoteTarget.from_koji, session.getBuildTarget, key[1], strict=False)


class RemoteTarget(TargetModel, RemoteObject):
    """
    Remote target object from Koji API
    """

    @classmethod
    def from_koji(cls, data: Optional[Dict[str, Any]]):
        if data is None:
            return None

        return cls(
            koji_id=data['id'],
            name=data['name'],
            build_tag=data['build_tag_name'],
            dest_tag=data['dest_tag_name'])


# The end.

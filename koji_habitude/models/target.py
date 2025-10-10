"""
koji-habitude - models.target

Target model for koji build target objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

from dataclasses import dataclass
from typing import Any, ClassVar, Optional, Sequence, TYPE_CHECKING

from koji import ClientSession, MultiCallSession, VirtualCall
from pydantic import Field

from .base import BaseKey, BaseObject
from .change import Change, ChangeReport, Create, Update

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

        dest_tag = self.obj.dest_tag or self.obj.name
        dest_tag = resolver.resolve(('tag', dest_tag))
        if dest_tag.is_phantom():
            return True

        return False

    def impl_apply(self, session: MultiCallSession) -> VirtualCall:
        return session.createBuildTarget(self.obj.name, self.obj.build_tag, self.obj.dest_tag or self.obj.name)

    def explain(self) -> str:
        dest_tag = self.obj.dest_tag or self.obj.name
        return f"Create target '{self.obj.name}' with build_tag '{self.obj.build_tag}' and dest_tag '{dest_tag}'"


@dataclass
class TargetEdit(Update):
    obj: 'Target'

    _skippable: ClassVar[bool] = True

    def skip_check_impl(self, resolver: 'Resolver') -> bool:
        build_tag = resolver.resolve(('tag', self.obj.build_tag))
        if build_tag.is_phantom():
            return True

        dest_tag = self.obj.dest_tag or self.obj.name
        dest_tag = resolver.resolve(('tag', dest_tag))
        if dest_tag.is_phantom():
            return True

        return False

    def impl_apply(self, session: MultiCallSession) -> VirtualCall:
        # thank you, koji-typing
        return session.editBuildTarget(self.obj.name, self.obj.name, self.obj.build_tag, self.obj.dest_tag or self.obj.name)

    def explain(self) -> str:
        dest_tag = self.obj.dest_tag or self.obj.name
        return f"Edit target '{self.obj.name}' to use build_tag '{self.obj.build_tag}' and dest_tag '{dest_tag}'"


class TargetChangeReport(ChangeReport):

    def impl_read(self, session: MultiCallSession):
        self._targetinfo: VirtualCall = self.obj.query_exists(session)


    def impl_compare(self):
        info = self._targetinfo.result
        if info is None:
            yield TargetCreate(self.obj)
            return

        build_tag = info['build_tag_name']
        dest_tag = info['dest_tag_name']

        if build_tag != self.obj.build_tag or dest_tag != self.obj.dest_tag:
            yield TargetEdit(self.obj)


class Target(BaseObject):
    """
    Koji build target object model.
    """

    typename: ClassVar[str] = "target"

    build_tag: str = Field(alias='build-tag')
    dest_tag: Optional[str] = Field(alias='dest-tag', default=None)


    def dependency_keys(self) -> Sequence[BaseKey]:
        """
        Return dependencies for this target.

        Targets depend on:
        - Build tag
        - Destination tag
        """

        return [
            ('tag', self.build_tag),
            ('tag', self.dest_tag or self.name),
        ]


    def change_report(self, resolver: 'Resolver') -> TargetChangeReport:
        return TargetChangeReport(self, resolver)


    @classmethod
    def check_exists(cls, session: ClientSession, key: BaseKey) -> Any:
        return session.getBuildTarget(key[1], strict=False)


# The end.

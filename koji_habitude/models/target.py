"""
koji-habitude - models.target

Target model for koji build target objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

from dataclasses import dataclass
from typing import Any, ClassVar, Optional, Sequence

from koji import ClientSession, MultiCallSession, VirtualCall
from pydantic import Field

from .base import BaseKojiObject, BaseKey
from .change import Change, ChangeReport


@dataclass
class TargetCreate(Change):
    name: str
    build_tag: str
    dest_tag: Optional[str] = None

    def impl_apply(self, session: MultiCallSession) -> VirtualCall:
        return session.createBuildTarget(self.name, self.build_tag, self.dest_tag or self.name)

    def explain(self) -> str:
        dest_tag = self.dest_tag or self.name
        return f"Create target '{self.name}' with build_tag '{self.build_tag}' and dest_tag '{dest_tag}'"


@dataclass
class TargetEdit(Change):
    name: str
    build_tag: str
    dest_tag: Optional[str] = None

    def impl_apply(self, session: MultiCallSession) -> VirtualCall:
        # thank you, koji-typing
        return session.editBuildTarget(self.name, self.name, self.build_tag, self.dest_tag or self.name)

    def explain(self) -> str:
        dest_tag = self.dest_tag or self.name
        return f"Edit target '{self.name}' to use build_tag '{self.build_tag}' and dest_tag '{dest_tag}'"


class TargetChangeReport(ChangeReport):

    def create_target(self):
        self.add(TargetCreate(self.obj.name, self.obj.build_tag, self.obj.dest_tag))


    def edit_target(self):
        self.add(TargetEdit(self.obj.name, self.obj.build_tag, self.obj.dest_tag))


    def impl_read(self, session: MultiCallSession):
        self._targetinfo: VirtualCall = session.getBuildTarget(self.obj.name, strict=False)


    def impl_compare(self):
        info = self._targetinfo.result
        if info is None:
            self.create_target()
            return

        build_tag = info['build_tag_name']
        dest_tag = info['dest_tag_name']

        if build_tag != self.obj.build_tag or dest_tag != self.obj.dest_tag:
            self.edit_target()


class Target(BaseKojiObject):
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


    def change_report(self) -> TargetChangeReport:
        return TargetChangeReport(self)


    @classmethod
    def check_exists(cls, session: ClientSession, key: BaseKey) -> Any:
        return session.getBuildTarget(key[1], strict=False)


# The end.

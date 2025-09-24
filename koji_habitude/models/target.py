"""
koji-habitude - models.target

Target model for koji build target objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

from typing import Any, ClassVar, Optional, Sequence

from pydantic import Field

from .base import BaseKojiObject, BaseKey


class Target(BaseKojiObject):
    """
    Koji build target object model.
    """

    typename: ClassVar[str] = "target"

    build_tag: str = Field(alias='build-tag')
    dest_tag: Optional[str] = Field(alias='dest-tag', default=None)


    def model_post_init(self, __context: Any):
        if self.dest_tag is None:
            self.dest_tag = self.name


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


# The end.

"""
koji-habitude - models.tag

Tag model for koji tag objects with inheritance and external repo dependencies.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

from typing import Any, ClassVar, Dict, List, Optional, Sequence

from pydantic import BaseModel, Field

from .base import BaseKey, BaseKojiObject


class InheritanceLink(BaseModel):
    name: str = Field(alias='name')
    priority: Optional[int] = Field(alias='priority', default=None)


class Tag(BaseKojiObject):
    """
    Koji tag object model.
    """

    typename: ClassVar[str] = "tag"
    _can_split: ClassVar[bool] = True

    arches: List[str] = Field(alias='arches', default_factory=list)
    maven: bool = Field(alias='maven', default=False)
    maven_include_all: bool = Field(alias='maven-include-all', default=False)
    extras: Dict[str, Any] = Field(alias='extras', default_factory=dict)
    groups: Dict[str, List[str]] = Field(alias='groups', default_factory=dict)

    inheritance: List[InheritanceLink] = Field(alias='inheritance', default_factory=list)
    external_repos: List[InheritanceLink] = Field(alias='external-repos', default_factory=list)


    def split(self) -> 'Tag':
        return Tag(name=self.name, arches=self.arches)


    def dependency_keys(self) -> Sequence[BaseKey]:
        """
        Return dependencies for this tag.

        Tags depend on:
        - Inheritance
        - External repositories
        """

        deps: List[BaseKey] = []

        # Check for inheritance dependencies
        for parent in self.inheritance:
            deps.append(('tag', parent.name))

        # Check for external repository dependencies
        for ext_repo in self.external_repos:
            deps.append(('external-repo', ext_repo.name))

        return deps


# The end.

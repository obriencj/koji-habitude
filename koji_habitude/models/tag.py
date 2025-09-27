"""
koji-habitude - models.tag

Tag model for koji tag objects with inheritance and external repo dependencies.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

from dataclasses import dataclass
from typing import Any, ClassVar, Dict, List, Optional, Sequence, Union

from koji import MultiCallSession, VirtualCall
from pydantic import BaseModel, Field, field_validator, model_validator

from .base import BaseKey, BaseKojiObject
from .change import Change, ChangeReport


@dataclass
class TagCreate(Change):
    name: str
    locked: bool
    permission: Optional[str]
    arches: List[str]
    maven_support: bool
    maven_include_all: bool

    def impl_apply(self, session: MultiCallSession):
        return session.createTag(
            self.name,
            locked=self.locked,
            perm=self.permission,
            arches=' '.join(self.arches),
            maven_support=self.maven_support,
            maven_include_all=self.maven_include_all)


@dataclass
class TagSetLocked(Change):
    name: str
    locked: bool

    def impl_apply(self, session: MultiCallSession):
        return session.editTag2(self.name, locked=self.locked)


@dataclass
class TagSetPermission(Change):
    name: str
    permission: Optional[str]

    def impl_apply(self, session: MultiCallSession):
        return session.editTag2(self.name, perm=self.permission)


@dataclass
class TagSetMaven(Change):
    name: str
    maven_support   : bool
    maven_include_all: bool

    def impl_apply(self, session: MultiCallSession):
        return session.editTag2(
            self.name,
            maven_support=self.maven_support,
            maven_include_all=self.maven_include_all)


@dataclass
class TagSetArches(Change):
    name: str
    arches: List[str]

    def impl_apply(self, session: MultiCallSession):
        return session.editTag2(self.name, arches=' '.join(self.arches))


@dataclass
class TagSetExtras(Change):
    name: str
    extras: Dict[str, Any]

    def impl_apply(self, session: MultiCallSession):
        return session.editTag2(self.name, extra=self.extras)


@dataclass
class TagAddGroup(Change):
    name: str
    group: str

    def impl_apply(self, session: MultiCallSession):
        return session.groupListAdd(self.name, self.group)


@dataclass
class TagRemoveGroup(Change):
    name: str
    group: str

    def impl_apply(self, session: MultiCallSession):
        return session.groupListRemove(self.name, self.group)


@dataclass
class TagAddGroupPackage(Change):
    name: str
    group: str
    package: str

    def impl_apply(self, session: MultiCallSession):
        return session.groupPackageListAdd(self.name, self.group, self.package)


@dataclass
class TagRemoveGroupPackage(Change):
    name: str
    group: str
    package: str

    def impl_apply(self, session: MultiCallSession):
        return session.groupPackageListRemove(self.name, self.group, self.package)


@dataclass
class TagAddInheritance(Change):
    name: str
    parent: str
    priority: int

    def impl_apply(self, session: MultiCallSession):
        data = [{'name': self.parent, 'priority': self.priority}]
        return session.setInheritanceData(self.name, data)


@dataclass
class TagRemoveInheritance(Change):
    name: str
    parent: str

    def impl_apply(self, session: MultiCallSession):
        data = [{'name': self.parent, 'delete link': True}]
        return session.setInheritanceData(self.name, data)


@dataclass
class TagAddExternalRepo(Change):
    name: str
    repo: str
    priority: int

    def impl_apply(self, session: MultiCallSession):
        return session.addExternalRepoToTag(self.name, self.repo, self.priority)


@dataclass
class TagRemoveExternalRepo(Change):
    name: str
    repo: str

    def impl_apply(self, session: MultiCallSession):
        return session.removeExternalRepoFromTag(self.name, self.repo)


class TagChangeReport(ChangeReport):

    def create_tag(self):
        self.add(TagCreate(
            self.obj.name,
            locked=self.obj.locked,
            permission=self.obj.permission,
            arches=self.obj.arches,
            maven_support=self.obj.maven_support,
            maven_include_all=self.obj.maven_include_all))

    def set_tag_locked(self):
        self.add(TagSetLocked(self.obj.name, self.obj.locked))

    def set_tag_permission(self):
        self.add(TagSetPermission(self.obj.name, self.obj.permission))

    def set_tag_arches(self):
        self.add(TagSetArches(self.obj.name, self.obj.arches))

    def set_tag_maven(self):
        self.add(TagSetMaven(self.obj.name, self.obj.maven_support, self.obj.maven_include_all))

    def set_tag_extras(self):
        self.add(TagSetExtras(self.obj.name, self.obj.extras))

    def add_group(self, group: str):
        self.add(TagAddGroup(self.obj.name, group))

    def remove_group(self, group: str):
        self.add(TagRemoveGroup(self.obj.name, group))

    def add_group_package(self, group: str, package: str):
        self.add(TagAddGroupPackage(self.obj.name, group, package))

    def add_group_packages(self, group: str, packages: List[str]):
        for package in packages:
            self.add_group_package(group, package)

    def remove_group_package(self, group: str, package: str):
        self.add(TagRemoveGroupPackage(self.obj.name, group, package))

    def add_inheritance(self, parent: 'InheritanceLink'):
        self.add(TagAddInheritance(self.obj.name, parent.name, parent.priority))

    def remove_inheritance(self, parent: 'InheritanceLink'):
        self.add(TagRemoveInheritance(self.obj.name, parent.name))

    def add_external_repo(self, repo: 'InheritanceLink'):
        self.add(TagAddExternalRepo(self.obj.name, repo.name, repo.priority))

    def remove_external_repo(self, repo: 'InheritanceLink'):
        self.add(TagRemoveExternalRepo(self.obj.name, repo.name))

    def impl_read(self, session: MultiCallSession):
        self._taginfo: VirtualCall = session.getTag(self.obj.name, strict=False)
        self._groups: VirtualCall = session.getTagGroups(self.obj.name, inherit=False)
        self._inheritance: VirtualCall = session.getInheritanceData(self.obj.name)
        self._external_repos: VirtualCall = session.getTagExternalRepos(tag_info=self.obj.name)

    def impl_compare(self):
        info = self._taginfo.result
        if info is None:
            self.create_tag()
            self.set_tag_extras()
            for group_name, group_packages in self.obj.groups.items():
                self.add_group(group_name)
                self.add_group_packages(group_name, group_packages)
            for parent in self.obj.inheritance:
                self.add_inheritance(parent)
            for repo in self.obj.external_repos:
                self.add_external_repo(repo)
            return

        if info['locked'] != self.obj.locked:
            self.set_tag_locked()
        if info['permission'] != self.obj.permission:
            self.set_tag_permission()
        if info['arches'] != self.obj.arches:
            self.set_tag_arches()
        if info['maven_support'] != self.obj.maven_support or \
           info['maven_include_all'] != self.obj.maven_include_all:
            self.set_tag_maven()
        if info['extras'] != self.obj.extras:
            self.set_tag_extras()

        groups = {group['name']: group for group in self._groups.result}
        for group_name, group_packages in self.obj.groups.items():
            if group_name not in groups:
                self.add_group(group_name)
                self.add_group_packages(group_name, group_packages)
            else:
                pkglist = groups[group_name]['packagelist']
                to_add = [pkg['package'] for pkg in pkglist if pkg['package'] not in group_packages]
                self.add_group_packages(group_name, to_add)
        # TODO: remove packages if exact_groups is True

        inher = {parent['name']: parent for parent in self._inheritance.result}
        for name, parent in inher.items():
            if name not in self.obj.inheritance:
                self.remove_inheritance(name)

        for parent in self.obj.inheritance:
            if parent.name not in inher:
                self.add_inheritance(parent)

        ext_repos = {repo['name']: repo for repo in self._external_repos.result}
        for name, repo in ext_repos.items():
            if name not in self.obj.external_repos:
                self.remove_external_repo(name)

        for repo in self.obj.external_repos:
            if repo.name not in ext_repos:
                self.add_external_repo(repo)


class TagGroupPackage(BaseModel):

    name: str = Field(alias='name')
    type: str = Field(alias='type', default='package')
    block: bool = Field(alias='block', default=False)

    @model_validator(mode='before')
    @classmethod
    def convert_from_simplified(cls, data: Any) -> Any:
        """
        Each package in a tag group can be specified as a simple string or as a full
        dictionary. If it's a string, the value is considered to be the name of the
        package, and the type is inferred from the string based on the presence of
        an '@' prefix. If it's a dictionary, it's expected to have a 'name' key,
        and optionally a 'type' and 'block' key.
        """

        if isinstance(data, str):
            if data.startswith('@'):
                data = data[1:]
                tp = 'group'
            else:
                tp = 'package'
            data = {
                'name': data,
                'type': tp,
                'block': False,
            }
        return data


class TagGroup(BaseModel):
    name: str = Field(alias='name')
    block: bool = Field(alias='block', default=False)
    packages: List[TagGroupPackage] = Field(alias='packages', default_factory=list)


class InheritanceLink(BaseModel):
    name: str = Field(alias='name')
    priority: int = Field(alias='priority')


class Tag(BaseKojiObject):
    """
    Koji tag object model.
    """

    typename: ClassVar[str] = "tag"
    _can_split: ClassVar[bool] = True

    locked: bool = Field(alias='locked', default=False)
    permission: Optional[str] = Field(alias='permission', default=None)
    arches: List[str] = Field(alias='arches', default_factory=list)
    maven_support: bool = Field(alias='maven-support', default=False)
    maven_include_all: bool = Field(alias='maven-include-all', default=False)
    extras: Dict[str, Any] = Field(alias='extras', default_factory=dict)
    groups: Dict[str, TagGroup] = Field(alias='groups', default_factory=dict)
    inheritance: List[InheritanceLink] = Field(alias='inheritance', default_factory=list)
    external_repos: List[InheritanceLink] = Field(alias='external-repos', default_factory=list)


    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)

        seen: Dict[int, InheritanceLink] = {}

        for parent in self.inheritance:
            if parent.priority in seen:
                raise ValueError(f"Duplicate priority {parent.priority} for tag {parent.name}")
            seen[parent.priority] = parent

        for parent in self.external_repos:
            if parent.priority in seen:
                raise ValueError(f"Duplicate priority {parent.priority} for external repo {parent.name}")
            seen[parent.priority] = parent


    @field_validator('groups', mode='before')
    @classmethod
    def convert_groups_from_simplified(cls, data: Any) -> Any:
        fixed: Dict[str, Dict[str, Any]] = {}

        if isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    item = {'name': item, 'packages': []}

                elif isinstance(item, dict):
                    if 'name' not in item:
                        raise ValueError(f"Group {item} must have a 'name' key")
                    if 'packages' not in item:
                        item['packages'] = []

                if item['name'] in fixed:
                    raise TypeError(f"Duplicate group {item['name']}")

                fixed[item['name']] = item

        elif isinstance(data, dict):
            for name, item in data.items():
                if isinstance(item, str):
                    raise ValueError(f"Group {name} must be a dictionary or list, got {type(item)}")

                elif isinstance(item, list):
                    item = {'name': name, 'packages': item}

                elif isinstance(item, dict):
                    oldname = item.setdefault('name', name)
                    if oldname != name:
                        raise TypeError(f"Group name mismatch: {oldname} != {name}")

                fixed[name] = item

        else:
            raise ValueError(f"Groups must be a dictionary or list, got {type(data)}")

        return fixed


    def split(self) -> 'Tag':
        return Tag(name=self.name, arches=self.arches)


    def dependency_keys(self) -> Sequence[BaseKey]:
        """
        Return dependencies for this tag.

        Tags depend on:
        - Permission
        - Inheritance
        - External repositories
        """

        deps: List[BaseKey] = []

        if self.permission:
            deps.append(('permission', self.permission))

        # Check for inheritance dependencies
        for parent in self.inheritance:
            deps.append(('tag', parent.name))

        # Check for external repository dependencies
        for ext_repo in self.external_repos:
            deps.append(('external-repo', ext_repo.name))

        return deps


    def change_report(self) -> TagChangeReport:
        return TagChangeReport(self)


# The end.

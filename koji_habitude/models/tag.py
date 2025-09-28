"""
koji-habitude - models.tag

Tag model for koji tag objects with inheritance and external repo dependencies.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

from dataclasses import dataclass
from typing import Any, ClassVar, Dict, List, Optional, Sequence, Union, Literal

from koji import ClientSession, MultiCallSession, VirtualCall
from pydantic import Field, field_validator, model_validator

from .base import BaseKey, BaseKojiObject, SubModel
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

    def explain(self) -> str:
        arches_str = ', '.join(self.arches)
        maven_info = ''
        if self.maven_support:
            maven_info = f" with Maven support (include_all={self.maven_include_all})"
        perm_info = f" with permission '{self.permission}'" if self.permission else ''
        locked_info = " (locked)" if self.locked else ''
        return f"Create tag '{self.name}' with arches [{arches_str}]{maven_info}{perm_info}{locked_info}"


@dataclass
class TagSetLocked(Change):
    name: str
    locked: bool

    def impl_apply(self, session: MultiCallSession):
        return session.editTag2(self.name, locked=self.locked)

    def explain(self) -> str:
        action = "Lock" if self.locked else "Unlock"
        return f"{action} tag '{self.name}'"


@dataclass
class TagSetPermission(Change):
    name: str
    permission: Optional[str]

    def impl_apply(self, session: MultiCallSession):
        return session.editTag2(self.name, perm=self.permission)

    def explain(self) -> str:
        if self.permission:
            return f"Set permission for tag '{self.name}' to '{self.permission}'"
        else:
            return f"Remove permission from tag '{self.name}'"


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

    def explain(self) -> str:
        if self.maven_support:
            include_all = "all" if self.maven_include_all else "specific"
            return f"Enable Maven support for tag '{self.name}' (include {include_all} artifacts)"
        else:
            return f"Disable Maven support for tag '{self.name}'"


@dataclass
class TagSetArches(Change):
    name: str
    arches: List[str]

    def impl_apply(self, session: MultiCallSession):
        return session.editTag2(self.name, arches=' '.join(self.arches))

    def explain(self) -> str:
        arches_str = ', '.join(self.arches)
        return f"Set arches for tag '{self.name}' to [{arches_str}]"


@dataclass
class TagSetExtras(Change):
    name: str
    extras: Dict[str, Any]

    def impl_apply(self, session: MultiCallSession):
        return session.editTag2(self.name, extra=self.extras)

    def explain(self) -> str:
        extras_str = ', '.join(f"{k}={v}" for k, v in self.extras.items())
        return f"Set extra fields for tag '{self.name}': {extras_str}"


@dataclass
class TagAddGroup(Change):
    name: str  # the tag name
    group: 'TagGroup'

    def impl_apply(self, session: MultiCallSession):
        return session.groupListAdd(
            self.name, self.group.name,
            description=self.group.description,
            block=self.group.block,
            force=True)

    def explain(self) -> str:
        block_info = " (blocked)" if self.group.block else ""
        desc_info = f" - {self.group.description}" if self.group.description else ""
        return f"Add group '{self.group.name}' to tag '{self.name}'{block_info}{desc_info}"


@dataclass
class TagUpdateGroup(Change):
    name: str  # the tag name
    group: 'TagGroup'

    def impl_apply(self, session: MultiCallSession):
        # same method is used for adding and editing groups
        return session.groupListAdd(
            self.name, self.group.name,
            description=self.group.description,
            block=self.group.block,
            force=True)

    def explain(self) -> str:
        block_info = " (blocked)" if self.group.block else ""
        desc_info = f" - {self.group.description}" if self.group.description else ""
        return f"Update group '{self.group.name}' in tag '{self.name}'{block_info}{desc_info}"


@dataclass
class TagRemoveGroup(Change):
    name: str   # the tag name
    group: str  # the group name

    def impl_apply(self, session: MultiCallSession):
        return session.groupListRemove(self.name, self.group)

    def explain(self) -> str:
        return f"Remove group '{self.group}' from tag '{self.name}'"


@dataclass
class TagAddGroupPackage(Change):
    name: str     # the tag name
    group: str    # the group name
    package: 'TagGroupPackage'

    def impl_apply(self, session: MultiCallSession):
        return session.groupPackageListAdd(
            self.name, self.group, self.package.name,
            block=self.package.block,
            force=True)

    def explain(self) -> str:
        block_info = " (blocked)" if self.package.block else ""
        return f"Add package '{self.package.name}' to group '{self.group}' in tag '{self.name}'{block_info}"


@dataclass
class TagUpdateGroupPackage(Change):
    name: str     # the tag name
    group: str    # the group name
    package: 'TagGroupPackage'

    def impl_apply(self, session: MultiCallSession):
        # same method is used for adding and updating packages
        return session.groupPackageListAdd(
            self.name, self.group, self.package.name,
            block=self.package.block,
            force=True)

    def explain(self) -> str:
        block_info = " (blocked)" if self.package.block else ""
        return f"Update package '{self.package.name}' in group '{self.group}' of tag '{self.name}'{block_info}"


@dataclass
class TagRemoveGroupPackage(Change):
    name: str     # the tag name
    group: str    # the group name
    package: str  # the package name

    def impl_apply(self, session: MultiCallSession):
        return session.groupPackageListRemove(self.name, self.group, self.package)

    def explain(self) -> str:
        return f"Remove package '{self.package}' from group '{self.group}' in tag '{self.name}'"


@dataclass
class TagAddInheritance(Change):
    name: str
    parent: 'InheritanceLink'

    def impl_apply(self, session: MultiCallSession):
        data = [{
            'parent_id': self.parent._parent_tag_id,
            'priority': self.parent.priority,
            # 'intransitive': self.parent.intransitive,
            'maxdepth': self.parent.maxdepth,
            'noconfig': self.parent.noconfig,
            'pkg_filter': self.parent.pkgfilter,
        }]
        return session.setInheritanceData(self.name, data)

    def explain(self) -> str:
        msg = f"with priority {self.parent.priority}"
        if self.parent.maxdepth is not None :
            msg += f" and maxdepth={self.parent.maxdepth}"
        if self.parent.noconfig is not None:
            msg += f" and noconfig={self.parent.noconfig}"
        if self.parent.pkgfilter is not None:
            msg += f" and pkgfilter={self.parent.pkgfilter}"
        return f"Add inheritance from '{self.parent}' to tag '{self.name}' {msg}"


@dataclass
class TagUpdateInheritance(TagAddInheritance):
    name: str
    parent: 'InheritanceLink'

    def explain(self) -> str:
        msg = f"with priority {self.parent.priority}"
        if self.parent.maxdepth is not None :
            msg += f" and maxdepth={self.parent.maxdepth}"
        if self.parent.noconfig is not None:
            msg += f" and noconfig={self.parent.noconfig}"
        if self.parent.pkgfilter is not None:
            msg += f" and pkgfilter={self.parent.pkgfilter}"
        return f"Update inheritance from '{self.parent}' to tag '{self.name}' {msg}"


@dataclass
class TagRemoveInheritance(Change):
    name: str
    parent_id: str

    def impl_apply(self, session: MultiCallSession):
        data = [{'parent_id': self.parent_id, 'delete link': True}]
        return session.setInheritanceData(self.name, data)

    def explain(self) -> str:
        return f"Remove inheritance from '{self.parent}' in tag '{self.name}'"


@dataclass
class TagAddExternalRepo(Change):
    name: str
    repo: str
    priority: int

    def impl_apply(self, session: MultiCallSession):
        return session.addExternalRepoToTag(self.name, self.repo, self.priority)

    def explain(self) -> str:
        return f"Add external repo '{self.repo}' to tag '{self.name}' with priority {self.priority}"


@dataclass
class TagRemoveExternalRepo(Change):
    name: str
    repo: str

    def impl_apply(self, session: MultiCallSession):
        return session.removeExternalRepoFromTag(self.name, self.repo)

    def explain(self) -> str:
        return f"Remove external repo '{self.repo}' from tag '{self.name}'"


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

    def add_group(self, group: 'TagGroup'):
        self.add(TagAddGroup(self.obj.name, group))

    def update_group(self, group: 'TagGroup'):
        self.add(TagUpdateGroup(self.obj.name, group))

    def remove_group(self, group: str):
        self.add(TagRemoveGroup(self.obj.name, group))

    def add_group_package(self, group: str, package: 'TagGroupPackage'):
        self.add(TagAddGroupPackage(self.obj.name, group, package))

    def update_group_package(self, group: str, package: 'TagGroupPackage'):
        self.add(TagUpdateGroupPackage(self.obj.name, group, package))

    def remove_group_package(self, group: str, package: str):
        self.add(TagRemoveGroupPackage(self.obj.name, group, package))

    def add_group_packages(self, group: str, packages: List['TagGroupPackage']):
        for package in packages:
            self.add_group_package(group, package)

    def update_group_packages(self, group: str, packages: List['TagGroupPackage']):
        for package in packages:
            self.update_group_package(group, package)

    def remove_group_packages(self, group: str, packages: List[str]):
        for package in packages:
            self.remove_group_package(group, package)

    def remove_group_package(self, group: str, package: str):
        self.add(TagRemoveGroupPackage(self.obj.name, group, package))

    def add_inheritance(self, parent: 'InheritanceLink'):
        self.add(TagAddInheritance(self.obj.name, parent))

    def update_inheritance(self, parent: 'InheritanceLink'):
        self.add(TagUpdateInheritance(self.obj.name, parent))

    def add_external_repo(self, repo: 'InheritanceLink'):
        self.add(TagAddExternalRepo(self.obj.name, repo.name, repo.priority))

    def remove_external_repo(self, repo: str):
        self.add(TagRemoveExternalRepo(self.obj.name, repo))

    def impl_read(self, session: MultiCallSession):
        self._taginfo: VirtualCall = self.obj.query_exists(session)
        self._groups: VirtualCall = None
        self._inheritance: VirtualCall = None
        self._external_repos: VirtualCall = None

        return self._impl_read_defer

    def _impl_read_defer(self, session: MultiCallSession):
        if self._taginfo.result is None:
            return

        self._groups = session.getTagGroups(self.obj.name, inherit=False, incl_blocked=True)
        self._inheritance = session.getInheritanceData(self.obj.name)
        self._external_repos = session.getTagExternalRepos(tag_info=self.obj.name)

    def impl_compare(self):
        info = self._taginfo.result
        if info is None:
            self.create_tag()
            self.set_tag_extras()
            for group_name, group in self.obj.groups.items():
                self.add_group(group)
                self.add_group_packages(group_name, group.packages)
            for parent in self.obj.parent_tags:
                self.add_inheritance(parent)
            for repo in self.obj.external_repos:
                self.add_external_repo(repo)
            return

        if info['locked'] != self.obj.locked:
            self.set_tag_locked()
        if info['perm'] != self.obj.permission:
            self.set_tag_permission()

        if info['arches'].split() != self.obj.arches:
            self.set_tag_arches()

        if info['maven_support'] != self.obj.maven_support or \
           info['maven_include_all'] != self.obj.maven_include_all:
            self.set_tag_maven()
        if info['extra'] != self.obj.extras:
            self.set_tag_extras()

        self._compare_groups()
        self._compare_inheritance()


    def _compare_inheritance(self):
        # Helper function to compare inheritance

        for parent in self.obj.parent_tags:
            tag = self.resolver.resolve(parent.key())
            tinfo = tag.exists
            if tinfo:
                parent._parent_tag_id = tinfo['id']

        koji_inher = {parent['parent_name']: parent for parent in self._inheritance.result}
        inher = {parent.name: parent for parent in self.obj.parent_tags}

        for name, parent in koji_inher.items():
            if name not in inher:
                self.remove_inheritance(parent['parent_id'])

        for name, parent in inher.items():
            if name not in koji_inher:
                self.add_inheritance(parent)
            else:
                if koji_inher['priority'] != parent.priority or \
                   koji_inher['maxdepth'] != parent.maxdepth or \
                   koji_inher['noconfig'] != parent.noconfig or \
                   koji_inher['pkg_filter'] != parent.pkgfilter:
                    self.update_inheritance(parent)

        koji_ext_repos = {repo['name']: repo for repo in self._external_repos.result}
        ext_repos = {repo.name: repo for repo in self.obj.external_repos}

        for name, repo in koji_ext_repos.items():
            if name not in ext_repos:
                self.remove_external_repo(name)

        for name, repo in ext_repos.items():
            if name not in koji_ext_repos:
                self.add_external_repo(repo)


    def _compare_groups(self):
        # Helper function to compare groups and their package content

        # TODO: we'll need to actually invoke addGroupReq vs. Package for these.
        # depending on the type. for now we just assume package for all.

        koji_groups = {group['name']: group for group in self._groups.result}
        for group_name, group in self.obj.groups.items():
            if group_name not in koji_groups:
                self.add_group(group)
                self.add_group_packages(group_name, group.packages)
                continue

            koji_group = koji_groups[group_name]
            if group.block != koji_group['blocked'] or \
               group.description != koji_group['description']:
                self.update_group(group)

            to_add : List[TagGroupPackage] = []
            to_update : List[TagGroupPackage] = []

            koji_pkgs = {pkg['package']: pkg for pkg in koji_group['packagelist']}
            for pkg in group.packages:
                if pkg.name not in koji_pkgs:
                    to_add.append(pkg)
                elif pkg.block != koji_pkgs[pkg.name]['blocked']:
                    to_update.append(pkg)

            if to_add:
                self.add_group_packages(group_name, to_add)

            if to_update:
                self.update_group_packages(group_name, to_update)

            if group.exact_packages:
                to_remove : List[str] = []
                pkgs = {pkg.name: pkg for pkg in group.packages}
                for pkg_name in koji_pkgs:
                    if pkg_name not in pkgs:
                        to_remove.append(pkg_name)
                if to_remove:
                    self.remove_group_packages(group_name, to_remove)

        if self.obj.exact_groups:
            for group_name in koji_groups:
                if group_name not in self.obj.groups:
                    self.remove_group(group_name)


class TagGroupPackage(SubModel):

    name: str = Field(alias='name')
    type: str = Field(alias='type', default='package')
    block: bool = Field(alias='blocked', default=False)

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
                # data = data[1:]
                # we don't use the @ prefix anymore, but we keep it for backwards compatibility
                tp = 'group'
            else:
                tp = 'package'
            data = {
                'name': data,
                'type': tp,
                'block': False,
            }
        return data


class TagGroup(SubModel):
    name: str = Field(alias='name')
    description: Optional[str] = Field(alias='description', default=None)
    block: bool = Field(alias='blocked', default=False)
    packages: List[TagGroupPackage] = Field(alias='packages', default_factory=list)
    exact_packages: bool = Field(alias='exact-packages', default=False)


class InheritanceLink(SubModel):
    name: str = Field(alias='name')
    priority: int = Field(alias='priority')
    type: Literal['tag', 'external-repo'] = Field(alias='type', default='tag')
    maxdepth: Optional[int] = Field(alias='max-depth', default=None)
    noconfig: bool = Field(alias='no-config', default=False)
    pkgfilter: Optional[str] = Field(alias='pkg-filter', default=None)

    _parent_tag_id: Optional[int] = None

    def key(self) -> BaseKey:
        return (self.type, self.name)

    @field_validator('pkgfilter', mode='before')
    @classmethod
    def convert_pkgfilter_from_simplified(cls, data: Any) -> Any:
        if isinstance(data, list):
            return f"^({'|'.join(data)})$"
        return data


class Tag(BaseKojiObject):
    """
    Koji tag object model.
    """

    typename: ClassVar[str] = "tag"
    _can_split: ClassVar[bool] = True

    locked: bool = Field(alias='lock', default=False)
    permission: Optional[str] = Field(alias='permission', default=None)
    arches: List[str] = Field(alias='arches', default_factory=list)
    maven_support: bool = Field(alias='maven-support', default=False)
    maven_include_all: bool = Field(alias='maven-include-all', default=False)
    extras: Dict[str, Any] = Field(alias='extras', default_factory=dict)
    groups: Dict[str, TagGroup] = Field(alias='groups', default_factory=dict)
    exact_groups: bool = Field(alias='exact-groups', default=False)
    inheritance: List[InheritanceLink] = Field(alias='inheritance', default_factory=list)


    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)

        seen: Dict[int, InheritanceLink] = {}

        for parent in self.inheritance:
            if parent.priority in seen:
                raise ValueError(f"Duplicate priority {parent.priority} for {parent.type} {parent.name}")
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


    @field_validator('inheritance', mode='before')
    @classmethod
    def convert_inheritance_from_simplified(cls, data: Any) -> Any:

        priorities = set()
        priority_increment = 10

        if isinstance(data, str):
            data = [{'name': data, 'type': 'tag', 'priority': 0}]

        elif isinstance(data, list):
            fixed: List[Dict[str, Any]] = []

            priority = 0
            for item in data:

                if isinstance(item, str):
                    item = {'name': item, 'type': 'tag', 'priority': priority}
                    fixed.append(item)
                    priorities.add(priority)
                    priority += priority_increment

                elif isinstance(item, dict):
                    priority = item.setdefault('priority', priority)
                    priorities.add(priority)

                    priority = max(priorities)
                    offset = priority_increment - (priority % priority_increment)
                    priority += offset

                    fixed.append(item)

                else:
                    # this will raise a validation error later on
                    fixed.append(item)

            data = fixed

        return data


    @property
    def parent_tags(self) -> List[InheritanceLink]:
        return [parent for parent in self.inheritance if parent.type == 'tag']


    @property
    def external_repos(self) -> List[InheritanceLink]:
        return [parent for parent in self.inheritance if parent.type == 'external-repo']


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
        for parent in self.parent_tags:
            deps.append(('tag', parent.name))

        # Check for external repository dependencies
        for ext_repo in self.external_repos:
            deps.append(('external-repo', ext_repo.name))

        return deps


    def change_report(self) -> TagChangeReport:
        return TagChangeReport(self)


    @classmethod
    def check_exists(cls, session: ClientSession, key: BaseKey) -> Any:
        return session.getTag(key[1], strict=False)


# The end.

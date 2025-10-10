"""
koji-habitude - models.tag

Tag model for koji tag objects with inheritance and external repo dependencies.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""


from dataclasses import dataclass
import logging
from typing import Any, ClassVar, Dict, List, Literal, Optional, Sequence, TYPE_CHECKING

from pydantic import Field, field_validator, model_validator

from koji import ClientSession, MultiCallNotReady, MultiCallSession, VirtualCall

from .base import BaseKey, BaseObject, SubModel
from .change import Change, ChangeReport, Create, Update, Add, Remove, Modify

if TYPE_CHECKING:
    from ..resolver import Resolver


logger = logging.getLogger(__name__)


def _compare_arches(koji_arches: Optional[str], arches: Optional[List[str]]) -> bool:
    if koji_arches is None:
        return arches is None
    elif arches is None:
        return False
    else:
        return set(koji_arches.split()) == set(arches)


@dataclass
class TagCreate(Create):
    obj: 'Tag'

    def impl_apply(self, session: MultiCallSession):
        res = session.createTag(
            self.obj.name,
            locked=self.obj.locked,
            arches=' '.join(self.obj.arches),
            maven_support=self.obj.maven_support,
            maven_include_all=self.obj.maven_include_all)

        # We have to queue up a new getTag call so that the Tag object can be
        # considered as existing, and so we can fetch its ID later. Tag
        # Inheritance is the only place that cannot operate except by using the
        # parent tag's ID (not by name)
        if self.obj._is_split:
            self.obj._original.query_exists(session)
        else:
            self.obj.query_exists(session)

        return res

    def summary(self) -> str:
        arches_info = ''
        if self.obj.arches:
            arches_str = ', '.join(self.obj.arches)
            arches_info = f" with arches [{arches_str}]"
        maven_info = ''
        if self.obj.maven_support or self.obj.maven_include_all:
            mvn = 'enabled' if self.obj.maven_support else 'disabled'
            maven_info = f" with Maven support {mvn} (include_all={self.obj.maven_include_all})"
        perm_info = f" with permission '{self.obj.permission}'" if self.obj.permission else ''
        locked_info = " (locked)" if self.obj.locked else ''
        return f"Create tag {self.obj.name}{perm_info}{locked_info}{arches_info}{maven_info}"


@dataclass
class SplitTagCheckup(Update):
    obj: 'Tag'

    def impl_apply(self, session: MultiCallSession):
        return self.obj.query_exists(session)

    def summary(self) -> str:
        return f"Post-split checkup"


@dataclass
class TagSetLocked(Update):
    obj: 'Tag'
    locked: bool

    def impl_apply(self, session: MultiCallSession):
        return session.editTag2(self.obj.name, locked=self.locked)

    def summary(self) -> str:
        action = "Lock" if self.locked else "Unlock"
        return f"{action} tag"


@dataclass
class TagSetPermission(Update):
    obj: 'Tag'
    permission: Optional[str]

    _skippable: ClassVar[bool] = True

    def skip_check_impl(self, resolver: 'Resolver') -> bool:
        permission = resolver.resolve(('permission', self.permission))
        return permission.is_phantom()

    def impl_apply(self, session: MultiCallSession):
        return session.editTag2(self.obj.name, perm=self.permission)

    def summary(self) -> str:
        return f"Set permission {self.permission}" if self.permission else "Clear permission"


@dataclass
class TagSetMaven(Update):
    obj: 'Tag'
    maven_support   : bool
    maven_include_all: bool

    def impl_apply(self, session: MultiCallSession):
        return session.editTag2(
            self.obj.name,
            maven_support=self.maven_support,
            maven_include_all=self.maven_include_all)

    def summary(self) -> str:
        return (("Enable" if self.maven_support else "Disable") + " Maven support," +
                ("Enable" if self.maven_include_all else "Disable") + " Maven include all")


@dataclass
class TagSetArches(Update):
    obj: 'Tag'
    arches: List[str]

    def impl_apply(self, session: MultiCallSession):
        return session.editTag2(self.obj.name, arches=' '.join(self.arches))

    def summary(self) -> str:
        if self.arches:
            arches_str = ', '.join(self.arches)
            return f"Set arches to [{arches_str}]"
        else:
            return "Clear arches"


@dataclass
class TagSetExtras(Update):
    obj: 'Tag'
    extras: Dict[str, Any]

    def impl_apply(self, session: MultiCallSession):
        return session.editTag2(self.obj.name, extra=self.extras)

    def summary(self) -> str:
        if self.extras:
            extras_str = ', '.join(f"{k}={v}" for k, v in self.extras.items())
            return f"Set extra fields: {extras_str}"
        else:
            return "Clear extra fields"


@dataclass
class TagAddGroup(Add):
    obj: 'Tag'
    group: 'TagGroup'

    def impl_apply(self, session: MultiCallSession):
        return session.groupListAdd(
            self.obj.name, self.group.name,
            description=self.group.description,
            block=self.group.block,
            force=True)

    def summary(self) -> str:
        block_info = " (blocked)" if self.group.block else ""
        desc_info = f" - {self.group.description}" if self.group.description else ""
        return f"Add group '{self.group.name}'{block_info}{desc_info}"


@dataclass
class TagUpdateGroup(Modify):
    obj: 'Tag'
    group: 'TagGroup'

    def impl_apply(self, session: MultiCallSession):
        # same method is used for adding and editing groups
        return session.groupListAdd(
            self.obj.name, self.group.name,
            description=self.group.description,
            block=self.group.block,
            force=True)

    def summary(self) -> str:
        block_info = " (blocked)" if self.group.block else ""
        desc_info = f" - {self.group.description}" if self.group.description else ""
        return f"Update group '{self.group.name}'{block_info}{desc_info}"


@dataclass
class TagRemoveGroup(Remove):
    obj: 'Tag'
    group: str

    def impl_apply(self, session: MultiCallSession):
        return session.groupListRemove(self.obj.name, self.group)

    def summary(self) -> str:
        return f"Remove group '{self.group}'"


@dataclass
class TagAddGroupPackage(Add):
    obj: 'Tag'
    group: str
    package: 'TagGroupPackage'

    def impl_apply(self, session: MultiCallSession):
        return session.groupPackageListAdd(
            self.obj.name, self.group, self.package.name,
            block=self.package.block,
            force=True)

    def summary(self) -> str:
        act = "Block" if self.package.block else "Add"
        return f"{act} package {self.package.name} in group {self.group}"


@dataclass
class TagUpdateGroupPackage(Modify):
    obj: 'Tag'
    group: str
    package: 'TagGroupPackage'

    def impl_apply(self, session: MultiCallSession):
        # same method is used for adding and updating packages
        return session.groupPackageListAdd(
            self.obj.name, self.group, self.package.name,
            block=self.package.block,
            force=True)

    def summary(self) -> str:
        act = "Block" if self.package.block else "Unblock"
        return f"{act} package {self.package.name} in group {self.group}"


@dataclass
class TagRemoveGroupPackage(Remove):
    obj: 'Tag'
    group: str
    package: str

    def impl_apply(self, session: MultiCallSession):
        return session.groupPackageListRemove(self.obj.name, self.group, self.package)

    def summary(self) -> str:
        return f"Remove package {self.package} from group {self.group}"


@dataclass
class TagAddInheritance(Add):
    obj: 'Tag'
    parent: 'InheritanceLink'

    _skippable: ClassVar[bool] = True

    def skip_check_impl(self, resolver: 'Resolver') -> bool:
        parent = resolver.resolve(self.parent.key())
        return parent.is_phantom()

    def impl_apply(self, session: MultiCallSession):
        data = [{
            'parent_id': self.parent._parent_tag_id,
            'priority': self.parent.priority,
            'intransitive': self.parent.intransitive,
            'maxdepth': self.parent.maxdepth,
            'noconfig': self.parent.noconfig,
            'pkg_filter': self.parent.pkgfilter,
        }]
        return session.setInheritanceData(self.obj.name, data)

    def summary(self) -> str:
        msg = f"with priority {self.parent.priority}"
        if self.parent.maxdepth is not None:
            msg += f" and maxdepth {self.parent.maxdepth}"
        if self.parent.noconfig is not None:
            msg += f" and noconfig {self.parent.noconfig}"
        if self.parent.pkgfilter is not None:
            msg += f" and pkgfilter {self.parent.pkgfilter!r}"
        return f"Add inheritance {self.parent.name} {msg}"

    def break_multicall(self, resolver: 'Resolver') -> bool:

        # quick explanation here. Adding to tag inheritance requires knowing the
        # parent tag's ID -- it's the only API in koji that has this behavior.
        # We have a hook at the end of the TagCreate's apply method which will
        # queue up a fetch of the newly created tag's ID, but until the MC
        # completes that value isn't available to us. What we're doing here is
        # using a resolver (which we got from the ChangeReport) to look up the
        # parent tag entry by its key, and then attempting to see if it exists.
        # If it does, we'll have the ID and we can continue. If checking raises
        # a MultiCallNotReady, then damnit we need to break out of the multicall
        # so it can complete and get us that value.

        logger.debug(f"Checking if TagAddInheritance ({self.obj.name}) needs to break out of multicall")

        tag = resolver.resolve(self.parent.key())
        logger.debug(f"Resolved parent tag '{self.parent.name}' to {tag}")

        tinfo = tag.exists()
        if tinfo is None:
            assert not tag.is_phantom()
            logger.debug(f"MultiCallNotReady, breaking out of multicall")
            return True

        logger.debug(f"Parent tag '{self.parent.name}' exists, ID: {tinfo['id']}")
        self.parent._parent_tag_id = tinfo['id']
        return False


@dataclass
class TagUpdateInheritance(Modify):
    obj: 'Tag'
    parent: 'InheritanceLink'
    parent_id: int

    def impl_apply(self, session: MultiCallSession):
        data = [{
            'parent_id': self.parent_id,
            'priority': self.parent.priority,
            'intransitive': self.parent.intransitive,
            'maxdepth': self.parent.maxdepth,
            'noconfig': self.parent.noconfig,
            'pkg_filter': self.parent.pkgfilter,
        }]
        return session.setInheritanceData(self.obj.name, data)

    def summary(self) -> str:
        msg = f"with priority {self.parent.priority}"
        if self.parent.maxdepth is not None :
            msg += f" and maxdepth {self.parent.maxdepth}"
        if self.parent.noconfig is not None:
            msg += f" and noconfig {self.parent.noconfig}"
        if self.parent.pkgfilter is not None:
            msg += f" and pkgfilter {self.parent.pkgfilter}"
        return f"Update inheritance {self.parent.name} {msg}"


@dataclass
class TagRemoveInheritance(Remove):
    obj: 'Tag'
    parent_id: str
    parent_name: str

    def impl_apply(self, session: MultiCallSession):
        data = [{'parent_id': self.parent_id, 'delete link': True}]
        return session.setInheritanceData(self.obj.name, data)

    def summary(self) -> str:
        return f"Remove inheritance {self.parent_name}"


@dataclass
class TagAddExternalRepo(Add):
    obj: 'Tag'
    repo: 'ExternalRepoLink'

    _skippable: ClassVar[bool] = True

    def skip_check_impl(self, resolver: 'Resolver') -> bool:
        repo = resolver.resolve(('external-repo', self.repo.name))
        return repo.is_phantom()

    def impl_apply(self, session: MultiCallSession):
        arches = ' '.join(self.repo.arches) if self.repo.arches else None
        return session.addExternalRepoToTag(
            self.obj.name, self.repo.name,
            priority=self.repo.priority,
            merge_mode=self.repo.merge_mode,
            arches=arches)

    def summary(self) -> str:
        msg = "with priority {self.repo.priority}"
        if self.repo.arches:
            msg += f" and arches {self.repo.arches!r}"
        if self.repo.merge_mode:
            msg += f" and merge_mode: {self.repo.merge_mode!r}"
        return f"Add external repo {self.repo.name} {msg}"


@dataclass
class TagUpdateExternalRepo(Modify):
    obj: 'Tag'
    repo: 'ExternalRepoLink'

    def impl_apply(self, session: MultiCallSession):
        arches = ' '.join(self.repo.arches) if self.repo.arches else None
        return session.editTagExternalRepo(
            self.obj.name, self.repo.name,
            priority=self.repo.priority,
            merge_mode=self.repo.merge_mode,
            arches=arches)

    def summary(self) -> str:
        msg = "with priority {self.repo.priority}"
        if self.repo.arches is not None:
            msg += f" and arches {self.repo.arches!r}"
        if self.repo.merge_mode is not None:
            msg += f" and merge_mode {self.repo.merge_mode!r}"
        return f"Update external repo {self.repo.name} {msg}"


@dataclass
class TagRemoveExternalRepo(Remove):
    obj: 'Tag'
    repo: str

    def impl_apply(self, session: MultiCallSession):
        return session.removeExternalRepoFromTag(self.obj.name, self.repo)

    def summary(self) -> str:
        return f"Remove external repo {self.repo}"


@dataclass
class TagPackageListAdd(Add):
    obj: 'Tag'
    package: 'PackageEntry'

    def impl_apply(self, session: MultiCallSession):
        arches = self.package.extra_arches
        arches = ' '.join(arches) if arches else None
        return session.packageListAdd(
            self.obj.name,
            self.package.name,
            owner=self.package.owner,
            block=self.package.block,
            extra_arches=arches,
            force=True)

    def summary(self) -> str:
        if self.package.block:
            return f"Block package {self.package.name}"
        else:
            info = " with owner {self.package.owner}" if self.package.owner else ""
            if self.package.extra_arches:
                arches_str = ', '.join(self.package.extra_arches)
                info += f" with extra_arches [{arches_str}]"
            return f"Add package {self.package.name}{info}"


@dataclass
class TagPackageListBlock(Add):
    obj: 'Tag'
    package: str

    def impl_apply(self, session: MultiCallSession):
        return session.packageListBlock(self.obj.name, self.package, force=True)

    def summary(self) -> str:
        return f"Block package {self.package}"


@dataclass
class TagPackageListUnblock(Modify):
    obj: 'Tag'
    package: str

    def impl_apply(self, session: MultiCallSession):
        return session.packageListUnblock(self.obj.name, self.package, force=True)

    def summary(self) -> str:
        return f"Unblock package {self.package}"


@dataclass
class TagPackageListSetOwner(Modify):
    obj: 'Tag'
    package: str
    owner: str

    def impl_apply(self, session: MultiCallSession):
        return session.packageListSetOwner(self.obj.name, self.package, self.owner, force=True)

    def summary(self) -> str:
        return f"Set package {self.package} owner to {self.owner}"


@dataclass
class TagPackageListSetArches(Modify):
    obj: 'Tag'
    package: str
    arches: List[str]

    def impl_apply(self, session: MultiCallSession):
        arches = ' '.join(self.arches) if self.arches else None
        return session.packageListSetArches(self.obj.name, self.package, arches, force=True)

    def summary(self) -> str:
        return f"Set package {self.package} extra_arches to {self.arches}"


@dataclass
class TagPackageListRemove(Remove):
    obj: 'Tag'
    package: str

    def impl_apply(self, session: MultiCallSession):
        return session.packageListRemove(self.obj.name, self.package, force=True)

    def summary(self) -> str:
        return f"Remove package {self.package}"


class TagChangeReport(ChangeReport):

    def impl_read(self, session: MultiCallSession):
        self._taginfo: VirtualCall = self.obj.query_exists(session)
        self._packagelist: VirtualCall = None
        self._groups: VirtualCall = None
        self._inheritance: VirtualCall = None
        self._external_repos: VirtualCall = None

        return self.impl_read_defer


    def impl_read_defer(self, session: MultiCallSession):
        if self._taginfo.result is None:
            return

        self._packagelist = session.listPackages(tagID=self.obj.name)
        self._groups = session.getTagGroups(self.obj.name, inherit=False, incl_blocked=True)
        self._inheritance = session.getInheritanceData(self.obj.name)
        self._external_repos = session.getTagExternalRepos(tag_info=self.obj.name)


    def impl_compare(self):
        info = self._taginfo.result
        if info is None:
            if self.obj.was_split():
                # we know we've split, but we don't exist yet, so we trust that we have
                # a split create for ourself already queued up in the same multicall.
                # In order for the tag inheritance hacks to work, we'll add a change
                # whose only job is to queue up a getTag call for ourself, so we can
                # answer for our existence later and give dependents our ID.
                yield SplitTagCheckup(self.obj)

            else:
                # we didn't need to split, so just do a normal create.
                yield TagCreate(self.obj)

            if self.obj.is_split():
                return

            if self.obj.permission:
                yield TagSetPermission(self.obj, self.obj.permission)
            if self.obj.extras:
                yield TagSetExtras(self.obj, self.obj.extras)
            for group_name, group in self.obj.groups.items():
                yield TagAddGroup(self.obj, group)
                for package in group.packages:
                    yield TagAddGroupPackage(self.obj, group_name, package)
            for parent in self.obj.inheritance:
                yield TagAddInheritance(self.obj, parent)
            for repo in self.obj.external_repos:
                yield TagAddExternalRepo(self.obj, repo)
            for package in self.obj.packages:
                yield TagPackageListAdd(self.obj, package)
            return

        if self.obj.is_split():
            return

        if info['locked'] != self.obj.locked:
            yield TagSetLocked(self.obj, self.obj.locked)
        if not _compare_arches(info['arches'], self.obj.arches):
            yield TagSetArches(self.obj, self.obj.arches)
        if info['maven_support'] != self.obj.maven_support or \
           info['maven_include_all'] != self.obj.maven_include_all:
            yield TagSetMaven(self.obj, self.obj.maven_support, self.obj.maven_include_all)

        if info['perm'] != self.obj.permission:
            yield TagSetPermission(self.obj, self.obj.permission)
        if info['extra'] != self.obj.extras:
            yield TagSetExtras(self.obj, self.obj.extras)

        yield from self._compare_packages()
        yield from self._compare_groups()
        yield from self._compare_inheritance()
        yield from self._compare_external_repos()


    def _compare_packages(self):
        koji_pkgs = {pkg['package_name']: pkg for pkg in self._packagelist.result}
        for package in self.obj.packages:
            if package.name not in koji_pkgs:
                yield TagPackageListAdd(self.obj, package)
            else:
                koji_pkg = koji_pkgs[package.name]
                if koji_pkg['blocked'] != package.block:
                    if package.block:
                        yield TagPackageListBlock(self.obj, package.name)
                    else:
                        yield TagPackageListUnblock(self.obj, package.name)
                if koji_pkg['owner_name'] != package.owner and package.owner is not None:
                    yield TagPackageListSetOwner(self.obj, package.name, package.owner)
                if not _compare_arches(koji_pkg['extra_arches'], package.extra_arches):
                    yield TagPackageListSetArches(self.obj, package.name, package.extra_arches)

        if self.obj.exact_packages:
            our_pkglist = {package.name for package in self.obj.packages}
            for package_name in koji_pkgs:
                if package_name not in our_pkglist:
                    yield TagPackageListRemove(self.obj, package_name)


    def _compare_inheritance(self):
        # Tag Inheritance

        # tag inheritance links are by ID, not name, so we need to ensure we
        # have those values.
        for parent in self.obj.inheritance:
            tag = self.resolver.resolve(parent.key())
            tinfo = tag.exists()
            if tinfo:
                parent._parent_tag_id = tinfo['id']
                logger.debug(f"Parent tag '{parent.name}' exists already, ID: {tinfo['id']}")
            else:
                logger.debug(f"Parent tag '{parent.name}' does not exist")

        koji_inher = {parent['name']: parent for parent in self._inheritance.result}
        inher = {parent.name: parent for parent in self.obj.inheritance}

        for name, parent in koji_inher.items():
            if name not in inher:
                yield TagRemoveInheritance(self.obj, parent['parent_id'], parent['name'])

        for name, parent in inher.items():
            if name not in koji_inher:
                yield TagAddInheritance(self.obj, parent)
            else:
                koji_parent = koji_inher[name]
                if koji_parent['priority'] != parent.priority or \
                   koji_parent['maxdepth'] != parent.maxdepth or \
                   koji_parent['noconfig'] != parent.noconfig or \
                   koji_parent['pkg_filter'] != parent.pkgfilter or \
                   koji_parent['intransitive'] != parent.intransitive:
                    yield TagUpdateInheritance(self.obj, parent, koji_parent['parent_id'])


    def _compare_external_repos(self):
        # External Repos
        koji_ext_repos = {repo['external_repo_name']: repo for repo in self._external_repos.result}
        ext_repos = {repo.name: repo for repo in self.obj.external_repos}

        for name, koji_repo in koji_ext_repos.items():
            if name not in ext_repos:
                yield TagRemoveExternalRepo(self.obj, name)
            else:
                repo = ext_repos[name]
                if koji_repo['priority'] != repo.priority or \
                   koji_repo['merge_mode'] != repo.merge_mode or \
                   not _compare_arches(koji_repo['arches'], repo.arches):
                    yield TagUpdateExternalRepo(self.obj, repo)

        for name, repo in ext_repos.items():
            if name not in koji_ext_repos:
                yield TagAddExternalRepo(self.obj, repo)


    def _compare_groups(self):
        # Helper function to compare groups and their package content

        # TODO: we'll need to actually invoke addGroupReq vs. Package for these.
        # depending on the type. for now we just assume package for all.

        koji_groups = {group['name']: group for group in self._groups.result}
        for group_name, group in self.obj.groups.items():
            if group_name not in koji_groups:
                yield TagAddGroup(self.obj, group)
                for package in group.packages:
                    yield TagAddGroupPackage(self.obj, group_name, package)
                continue

            koji_group = koji_groups[group_name]
            if group.block != koji_group['blocked'] or \
               group.description != koji_group['description']:
                yield TagUpdateGroup(self.obj, group)

            to_add : List[TagGroupPackage] = []
            to_update : List[TagGroupPackage] = []

            koji_pkgs = {pkg['package']: pkg for pkg in koji_group['packagelist']}
            for pkg in group.packages:
                if pkg.name not in koji_pkgs:
                    to_add.append(pkg)
                elif pkg.block != koji_pkgs[pkg.name]['blocked']:
                    to_update.append(pkg)

            for package in to_add:
                yield TagAddGroupPackage(self.obj, group_name, package)

            for package in to_update:
                yield TagUpdateGroupPackage(self.obj, group_name, package)

            if group.exact_packages:
                to_remove : List[str] = []
                pkgs = {pkg.name: pkg for pkg in group.packages}
                for pkg_name in koji_pkgs:
                    if pkg_name not in pkgs:
                        to_remove.append(pkg_name)
                for pkg_name in to_remove:
                    yield TagRemoveGroupPackage(self.obj, group_name, pkg_name)

        if self.obj.exact_groups:
            for group_name in koji_groups:
                if group_name not in self.obj.groups:
                    yield TagRemoveGroup(self.obj, group_name)


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


class PackageEntry(SubModel):

    name: str = Field(alias='name')
    block: bool = Field(alias='blocked', default=False)
    owner: Optional[str] = Field(alias='owner', default=None)
    extra_arches: Optional[List[str]] = Field(alias='extra-arches', default=None)


class InheritanceLink(SubModel):

    name: str = Field(alias='name')
    priority: int = Field(alias='priority')
    maxdepth: Optional[int] = Field(alias='max-depth', default=None)
    noconfig: bool = Field(alias='no-config', default=False)
    pkgfilter: str = Field(alias='pkg-filter', default='')
    intransitive: bool = Field(alias='intransitive', default=False)

    _parent_tag_id: Optional[int] = None


    @field_validator('pkgfilter', mode='before')
    @classmethod
    def convert_pkgfilter_from_simplified(cls, data: Any) -> Any:
        if isinstance(data, list):
            return f"^({'|'.join(data)})$"
        return data


    def key(self) -> BaseKey:
        return ('tag', self.name)


class ExternalRepoLink(SubModel):

    name: str = Field(alias='name')
    priority: int = Field(alias='priority')

    arches: Optional[List[str]] = Field(alias='arches', default=None)
    merge_mode: Literal['koji', 'simple', 'bare'] = Field(alias='merge-mode', default='koji')


    def key(self) -> BaseKey:
        return ('external-repo', self.name)


def _simplified_link(data: Any) -> Any:
    """
    we allow the inheritance and external-repo fields to be specified in a
    simplified manner, as a strings (for a single parent), a list of strings
    (for automatically-priority-numbered parents), or as a list of full
    dictionaries representing the individual settings of each parent.
    """

    priorities = set()
    priority_increment = 10

    if isinstance(data, str):
        data = [{'name': data, 'priority': 0}]

    elif isinstance(data, list):
        fixed: List[Dict[str, Any]] = []

        priority = 0
        for item in data:

            if isinstance(item, str):
                item = {'name': item, 'priority': priority}
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


class Tag(BaseObject):
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
    external_repos: List[ExternalRepoLink] = Field(alias='external-repos', default_factory=list)

    packages: List[PackageEntry] = Field(alias='packages', default_factory=list)
    exact_packages: bool = Field(alias='exact-packages', default=False)

    _auto_split: ClassVar[bool] = True

    _original: Optional['Tag'] = None


    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)

        seen = {}
        for parent in self.inheritance:
            if parent.priority in seen:
                raise ValueError(f"Duplicate tag priority {parent.priority} for {parent.name}")
            seen[parent.priority] = parent

        seen = {}
        for parent in self.external_repos:
            if parent.priority in seen:
                raise ValueError(f"Duplicate external repo priority {parent.priority} for {parent.name}")
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
        return _simplified_link(data)


    @field_validator('external_repos', mode='before')
    @classmethod
    def convert_external_repos_from_simplified(cls, data: Any) -> Any:
        return _simplified_link(data)


    @field_validator('packages', mode='before')
    @classmethod
    def convert_packages_from_simplified(cls, data: Any) -> Any:
        """
        we allow the packages field to be specified in a simplified manner, as a
        list of strings or a list of dictionaries. If it's a string, the value is
        considered to be the name of the package.
        """

        if isinstance(data, str):
            data = [{'name': data}]

        elif isinstance(data, list):
            fixed: List[Dict[str, Any]] = []
            for item in data:
                if isinstance(item, str):
                    item = {'name': item}
                fixed.append(item)
            data = fixed

        return data


    @field_validator('packages', mode='after')
    @classmethod
    def merge_packages(cls, data: Any) -> Any:
        seen = {}
        for package in data:
            if package.name in seen:
                logger.warning(f"Duplicate package {package.name}, overriding with new value")
            seen[package.name] = package
        return list(seen.values())


    def split(self) -> 'Tag':
        # normally a split only creates the object by name, and we worry about doing
        # full configuration in a separate step. For tag we'll do a full creation in
        # the split step, and have some extra logic handling in the change report
        # to queue up our self-lookup.

        child = Tag(
            name=self.name,
            arches=self.arches,
            locked=self.locked,
            maven_support=self.maven_support,
            maven_include_all=self.maven_include_all,
        )
        child._is_split = True
        child._original = self
        self._was_split = True
        return child


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
            deps.append(parent.key())

        # Check for external repository dependencies
        for ext_repo in self.external_repos:
            deps.append(ext_repo.key())

        for package in self.packages:
            if package.owner:
                deps.append(('user', package.owner))

        return deps


    def change_report(self, resolver: 'Resolver') -> TagChangeReport:
        return TagChangeReport(self, resolver)


    @classmethod
    def check_exists(cls, session: ClientSession, key: BaseKey) -> Any:
        logger.debug(f"Checking if tag '{key[1]}' exists")
        return session.getTag(key[1], strict=False)


# The end.

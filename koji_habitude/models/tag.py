"""
koji-habitude - models.tag

Tag model for koji tag objects with inheritance and external repo dependencies.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 3.5 Sonnet via Cursor
"""


import logging
from operator import itemgetter
from dataclasses import dataclass
from typing import (TYPE_CHECKING, Any, ClassVar, Dict, Iterable, List,
                    Literal, Optional, Sequence)

from koji import MultiCallSession, VirtualCall

from ..koji import call_processor, promise_call, VirtualPromise
from .base import BaseKey, CoreModel, CoreObject, RemoteObject, SubModel
from .change import Add, Change, ChangeReport, Create, Modify, Remove, Update
from .compat import Field, field_validator

if TYPE_CHECKING:
    from ..resolver import Resolver


logger = logging.getLogger(__name__)


def compare_arches(arches_a: Optional[List[str]], arches_b: Optional[List[str]]) -> bool:
    if arches_a is None:
        return arches_b is None
    elif arches_b is None:
        return False
    else:
        return set(arches_a) == set(arches_b)


def split_arches(arches: Optional[str], allow_none: bool = False) -> Optional[List[str]]:
    if arches is None:
        return None if allow_none else []
    else:
        return arches.split()


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
            self.obj._original.load_remote(session, reload=True)
        else:
            self.obj.load_remote(session, reload=True)

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
        locked_info = " (locked)" if self.obj.locked else ''
        return f"Create tag {self.obj.name}{locked_info}{arches_info}{maven_info}"


@dataclass
class SplitTagCheckup(Update):
    obj: 'Tag'

    def impl_apply(self, session: MultiCallSession):
        return self.obj.load_remote(session)

    def summary(self) -> str:
        return "Post-split checkup"


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
class TagAddExtra(Add):
    obj: 'Tag'
    key: str
    value: Any

    def impl_apply(self, session: MultiCallSession):
        return session.editTag2(self.obj.name, extra={self.key: self.value})

    def summary(self) -> str:
        return f"Add extra field {self.key} = {self.value}"


@dataclass
class TagUpdateExtra(Modify):
    obj: 'Tag'
    key: str
    value: Any

    def impl_apply(self, session: MultiCallSession):
        return session.editTag2(self.obj.name, extra={self.key: self.value})

    def summary(self) -> str:
        return f"Update extra field {self.key} = {self.value}"


@dataclass
class TagRemoveExtra(Remove):
    obj: 'Tag'
    key: str

    def impl_apply(self, session: MultiCallSession):
        return session.editTag2(self.obj.name, remove_extra=[self.key])

    def summary(self) -> str:
        return f"Remove extra field {self.key}"


@dataclass
class TagBlockExtra(Add):
    obj: 'Tag'
    key: str

    def impl_apply(self, session: MultiCallSession):
        return session.editTag2(self.obj.name, block_extra=[self.key])

    def summary(self) -> str:
        return f"Block extra field {self.key}"


@dataclass
class TagUnblockExtra(Remove):
    obj: 'Tag'
    key: str

    def impl_apply(self, session: MultiCallSession):
        # we can't directly remove a block, we have to set it to a value and
        # then remove it
        session.editTag2(self.obj.name, extra={self.key: None})
        return session.editTag2(self.obj.name, remove_extra=[self.key])

    def summary(self) -> str:
        return f"Unblock extra field {self.key}"


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

        # quick explanation here. Adding to tag inheritance requires
        # knowing the parent tag's ID -- it's the only API in koji
        # that has this behavior.  We have a hook at the end of the
        # TagCreate's apply method which will queue up a fetch of the
        # newly created tag's ID, but until the MC completes that
        # value isn't available to us. What we're doing here is using
        # a resolver (which we got from the ChangeReport) to look up
        # the parent tag entry by its key, and then attempting to see
        # if it exists.  If it does, we'll have the ID and we can
        # continue. If checking raises a MultiCallNotReady, then
        # damnit we need to break out of the multicall so it can
        # complete and get us that value.

        logger.debug(f"Checking if TagAddInheritance ({self.obj.name}) needs to break out of multicall")

        tag = resolver.resolve(self.parent.key())
        logger.debug(f"Resolved parent tag '{self.parent.name}' to {tag}")

        tinfo = tag.remote()
        if tinfo is None:
            if tag.is_phantom():
                logger.debug(f"Parent tag '{self.parent.name}' is phantom, skipping")
                return False

            logger.debug("MultiCallNotReady, breaking out of multicall")
            return True

        logger.debug(f"Parent tag '{self.parent.name}' exists, ID: {tinfo.koji_id}")
        self.parent._parent_tag_id = tinfo.koji_id
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
        msg = f"with priority {self.repo.priority}"
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
        msg = f"with priority {self.repo.priority}"
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

    _phantom_owner: bool = False

    _skippable: ClassVar[bool] = True

    def skip_check_impl(self, resolver: 'Resolver') -> bool:
        # We don't actually skip, but we do set the owner to None if it's a
        # phantom
        owner = resolver.resolve(('user', self.package.owner))
        self._phantom_owner = owner.is_phantom()
        return False

    def impl_apply(self, session: MultiCallSession):
        arches_list = self.package.extra_arches
        arches = ' '.join(arches_list) if arches_list else None
        owner = self.package.owner if not self._phantom_owner else None
        return session.packageListAdd(
            self.obj.name,
            self.package.name,
            owner=owner,
            block=self.package.block,
            extra_arches=arches,
            force=True)

    def summary(self) -> str:
        if self.package.block:
            return f"Block package {self.package.name}"
        else:
            owner = self.package.owner if not self._phantom_owner else None
            info = f" with owner {owner}" if owner else ""
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

    _skippable: ClassVar[bool] = True

    def skip_check_impl(self, resolver: 'Resolver') -> bool:
        owner = resolver.resolve(('user', self.owner))
        return owner.is_phantom()

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

    obj: 'Tag'


    def impl_compare(self) -> Iterable[Change]:
        remote = self.obj.remote()
        if not remote:
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
                for grp_package in group.packages:
                    yield TagAddGroupPackage(self.obj, group_name, grp_package)
            for parent in self.obj.inheritance:
                yield TagAddInheritance(self.obj, parent)
            for repo in self.obj.external_repos:
                yield TagAddExternalRepo(self.obj, repo)
            for package in self.obj.packages:
                yield TagPackageListAdd(self.obj, package)
            return

        if self.obj.is_split():
            return

        if remote.locked != self.obj.locked:
            yield TagSetLocked(self.obj, self.obj.locked)

        if not compare_arches(remote.arches, self.obj.arches):
            yield TagSetArches(self.obj, self.obj.arches)

        if remote.maven_support != self.obj.maven_support or \
           remote.maven_include_all != self.obj.maven_include_all:
            yield TagSetMaven(self.obj, self.obj.maven_support, self.obj.maven_include_all)

        if remote.permission != self.obj.permission:
            yield TagSetPermission(self.obj, self.obj.permission)

        yield from self._compare_extras()
        yield from self._compare_packages()
        yield from self._compare_groups()
        yield from self._compare_inheritance()
        yield from self._compare_external_repos()


    def _compare_extras(self) -> Iterable[Change]:
        remote = self.obj.remote()

        if remote.extras == self.obj.extras:
            return

        if not remote.extras:
            yield TagSetExtras(self.obj, self.obj.extras)
            return

        exact_extras = self.obj.exact_extras
        for key, value in self.obj.extras.items():
            if key not in remote.extras:
                yield TagAddExtra(self.obj, key, value)
            elif remote.extras[key] != value:
                yield TagUpdateExtra(self.obj, key, value)

        if exact_extras:
            for key in remote.extras:
                if key not in self.obj.extras:
                    yield TagRemoveExtra(self.obj, key)

        for key in self.obj.block_extras:
            if key not in remote.block_extras:
                if key not in self.obj.extras:
                    yield TagBlockExtra(self.obj, key)

        if exact_extras:
            for key in remote.block_extras:
                if key not in self.obj.block_extras:
                    if key not in self.obj.extras:
                        yield TagUnblockExtra(self.obj, key)


    def _compare_packages(self) -> Iterable[Change]:
        remote = self.obj.remote()
        koji_pkgs = {pkg.name: pkg for pkg in remote.packages}

        for package in self.obj.packages:
            if package.name not in koji_pkgs:
                yield TagPackageListAdd(self.obj, package)
            else:
                koji_pkg = koji_pkgs[package.name]
                if koji_pkg.block != package.block:
                    if package.block:
                        yield TagPackageListBlock(self.obj, package.name)
                    else:
                        yield TagPackageListUnblock(self.obj, package.name)
                if koji_pkg.owner != package.owner and package.owner is not None:
                    yield TagPackageListSetOwner(self.obj, package.name, package.owner)
                if not compare_arches(koji_pkg.extra_arches, package.extra_arches):
                    yield TagPackageListSetArches(self.obj, package.name, package.extra_arches)

        if self.obj.exact_packages:
            our_pkglist = {package.name for package in self.obj.packages}
            for package_name in koji_pkgs:
                if package_name not in our_pkglist:
                    yield TagPackageListRemove(self.obj, package_name)


    def _compare_inheritance(self) -> Iterable[Change]:
        # Tag Inheritance
        remote = self.obj.remote()

        # tag inheritance links are by ID, not name, so we need to ensure we
        # have those values.
        for parent in self.obj.inheritance:
            tag = self.resolver.resolve(parent.key())
            tremote = tag.remote()
            if tremote:
                parent._parent_tag_id = tremote.koji_id
                logger.debug(f"Parent tag '{parent.name}' exists already, ID: {tremote.koji_id}")
            else:
                logger.debug(f"Parent tag '{parent.name}' does not exist")

        koji_inher = {parent.name: parent for parent in remote.inheritance}
        inher = {parent.name: parent for parent in self.obj.inheritance}

        for name, parent in koji_inher.items():
            if name not in inher:
                yield TagRemoveInheritance(self.obj, parent._parent_tag_id, parent.name)

        for name, parent in inher.items():
            if name not in koji_inher:
                yield TagAddInheritance(self.obj, parent)
            else:
                koji_parent = koji_inher[name]
                if koji_parent.priority != parent.priority or \
                   koji_parent.maxdepth != parent.maxdepth or \
                   koji_parent.noconfig != parent.noconfig or \
                   koji_parent.pkgfilter != parent.pkgfilter or \
                   koji_parent.intransitive != parent.intransitive:
                    yield TagUpdateInheritance(self.obj, parent, koji_parent._parent_tag_id)


    def _compare_external_repos(self) -> Iterable[Change]:
        # External Repos
        remote = self.obj.remote()

        koji_ext_repos = {repo.name: repo for repo in remote.external_repos}
        ext_repos = {repo.name: repo for repo in self.obj.external_repos}

        for name, koji_repo in koji_ext_repos.items():
            if name not in ext_repos:
                yield TagRemoveExternalRepo(self.obj, name)
            else:
                repo = ext_repos[name]
                if koji_repo.priority != repo.priority or \
                   koji_repo.merge_mode != repo.merge_mode or \
                   not compare_arches(koji_repo.arches, repo.arches):
                    yield TagUpdateExternalRepo(self.obj, repo)

        for name, repo in ext_repos.items():
            if name not in koji_ext_repos:
                yield TagAddExternalRepo(self.obj, repo)


    def _compare_groups(self) -> Iterable[Change]:
        # Helper function to compare groups and their package content
        remote = self.obj.remote()
        # TODO: we'll need to actually invoke addGroupReq vs. Package for these.
        # depending on the type. for now we just assume package for all.

        koji_groups = remote.groups
        for group_name, group in self.obj.groups.items():
            if group_name not in koji_groups:
                yield TagAddGroup(self.obj, group)
                for package in group.packages:
                    yield TagAddGroupPackage(self.obj, group_name, package)
                continue

            koji_group = koji_groups[group_name]
            if group.block != koji_group.block or \
               group.description != koji_group.description:
                yield TagUpdateGroup(self.obj, group)

            to_add : List[TagGroupPackage] = []
            to_update : List[TagGroupPackage] = []

            koji_pkgs = {pkg.name: pkg for pkg in koji_group.packages}
            for pkg in group.packages:
                if pkg.name not in koji_pkgs:
                    to_add.append(pkg)
                elif pkg.block != koji_pkgs[pkg.name].block:
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


class TagGroupModel(SubModel):

    name: str = Field(alias='name')
    description: Optional[str] = Field(alias='description', default=None)
    block: bool = Field(alias='blocked', default=False)
    packages: List[TagGroupPackage] = Field(alias='packages', default_factory=list)


class TagGroup(TagGroupModel):

    exact_packages: bool = Field(alias='exact-packages', default=False)

    @field_validator("packages", mode='before')
    def convert_from_simplified(cls, data: Any) -> Any:
        """
        Each package in a tag group can be specified as a simple string or as a full
        dictionary. If it's a string, the value is considered to be the name of the
        package, and the type is inferred from the string based on the presence of
        an '@' prefix. If it's a dictionary, it's expected to have a 'name' key,
        and optionally a 'type' and 'block' key.
        """

        fixed: List[Dict[str, Any]] = []

        for item in data:
            if isinstance(item, str):
                if item.startswith('@'):
                    # data = data[1:]
                    # we don't use the @ prefix anymore, but we keep it for backwards compatibility
                    tp = 'group'
                else:
                    tp = 'package'
                item = {
                    'name': item,
                    'type': tp,
                    'block': False,
                }
            fixed.append(item)

        return fixed


class RemoteTagGroup(TagGroupModel):
    pass


class PackageEntry(SubModel):

    name: str = Field(alias='name')
    block: bool = Field(alias='blocked', default=False)
    owner: Optional[str] = Field(alias='owner', default=None)
    extra_arches: List[str] = Field(alias='extra-arches', default_factory=list)


class InheritanceLink(SubModel):

    name: str = Field(alias='name')
    priority: int = Field(alias='priority')
    maxdepth: Optional[int] = Field(alias='max-depth', default=None)
    noconfig: bool = Field(alias='no-config', default=False)
    pkgfilter: str = Field(alias='pkg-filter', default='')
    intransitive: bool = Field(alias='intransitive', default=False)

    _parent_tag_id: Optional[int] = None


    @field_validator('pkgfilter', mode='before')
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


class TagModel(CoreModel):
    """
    Field definitions for Tag objects
    """

    typename: ClassVar[str] = "tag"

    locked: bool = Field(alias='lock', default=False)
    permission: Optional[str] = Field(alias='permission', default=None)
    arches: List[str] = Field(alias='arches', default_factory=list)
    maven_support: bool = Field(alias='maven-support', default=False)
    maven_include_all: bool = Field(alias='maven-include-all', default=False)
    extras: Dict[str, Any] = Field(alias='extras', default_factory=dict)
    block_extras: List[str] = Field(alias='blocked-extras', default_factory=list)
    groups: Dict[str, TagGroup] = Field(alias='groups', default_factory=dict)
    inheritance: List[InheritanceLink] = Field(alias='inheritance', default_factory=list)
    external_repos: List[ExternalRepoLink] = Field(alias='external-repos', default_factory=list)
    packages: List[PackageEntry] = Field(alias='packages', default_factory=list)


    def dependency_keys(self) -> Sequence[BaseKey]:
        deps: List[BaseKey] = []

        if self.permission:
            deps.append(('permission', self.permission))

        deps.extend(parent.key() for parent in self.inheritance)
        deps.extend(ext_repo.key() for ext_repo in self.external_repos)

        # set doesn't preserve order, so we'll use a dict like a set
        owners = dict.fromkeys(package.owner for package in self.packages if package.owner)
        deps.extend(('user', owner) for owner in owners.keys())

        return deps


    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        data = super().model_dump(**kwargs)
        # we do all the membership checks because if exclude_defaults is True,
        # then some of these might not be present in the data.

        if 'arches' in data:
            data['arches'] = sorted(data['arches'])

        if 'packages' in data:
            data['packages'] = sorted(
                data['packages'], key=itemgetter('name'))

        if 'inheritance' in data:
            data['inheritance'] = sorted(
                data['inheritance'], key=itemgetter('priority'))

        if 'external-repos' in data:
            data['external-repos'] = sorted(
                data['external-repos'], key=itemgetter('priority'))

        # we sort this here instead of on the TagGroup model because
        # we support pydantic v1 and v2, and while we add a model_dump
        # method as an adapter for v1, it doesn't internally call the
        # model_dump method on the TagGroup in that case.
        if 'groups' in data:
            for group in data['groups'].values():
                if 'packages' in group:
                    group['packages'] = sorted(
                        group['packages'], key=itemgetter('name'))

        return data


class Tag(TagModel, CoreObject):
    """
    Local tag object from YAML.
    """

    exact_extras: bool = Field(alias='exact-extras', default=False)
    exact_groups: bool = Field(alias='exact-groups', default=False)
    exact_packages: bool = Field(alias='exact-packages', default=False)

    _can_split: ClassVar[bool] = True
    _auto_split: ClassVar[bool] = True

    _original: Optional['Tag'] = None


    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)

        seen: Dict[int, Any] = {}
        for parent in self.inheritance:
            if parent.priority in seen:
                raise ValueError(f"Duplicate tag priority {parent.priority} for {parent.name}")
            seen[parent.priority] = parent

        seen = {}
        for repo in self.external_repos:
            if repo.priority in seen:
                raise ValueError(f"Duplicate external repo priority {repo.priority} for {repo.name}")
            seen[repo.priority] = repo


    @field_validator('groups', mode='before')
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
                    raise ValueError(f"Duplicate group: {item['name']}")

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
                        raise ValueError(f"Group name mismatch: {oldname} != {name}")

                fixed[name] = item

        else:
            raise ValueError(f"Groups must be a dictionary or list, got {type(data)}")

        return fixed


    @field_validator('inheritance', mode='before')
    def convert_inheritance_from_simplified(cls, data: Any) -> Any:
        return _simplified_link(data)


    @field_validator('external_repos', mode='before')
    def convert_external_repos_from_simplified(cls, data: Any) -> Any:
        return _simplified_link(data)


    @field_validator('packages', mode='before')
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


    def change_report(self, resolver: 'Resolver') -> TagChangeReport:
        return TagChangeReport(self, resolver)


    @classmethod
    def query_remote(cls, session: MultiCallSession, key: BaseKey) -> 'VirtualCall[RemoteTag]':
        return call_processor(RemoteTag.from_koji, session.getTag, key[1], strict=False, blocked=True)


class RemoteTag(TagModel, RemoteObject):
    """
    Remote tag object from Koji API
    """

    groups: Dict[str, RemoteTagGroup] = Field(alias='groups', default_factory=dict)  # type: ignore


    @classmethod
    def from_koji(cls, data: Optional[Dict[str, Any]]):
        if data is None:
            return None

        blocked_extras = []
        pure_extras = {}
        for key, value in data.get('extra', {}).items():
            if not isinstance(value, list) or len(value) != 2:
                # someone invoked this with the extras field missing the blocked data
                raise ValueError(f"Extra items must be `[blocked, value]`, got {value!r}")

            blocked, val = value
            if blocked:
                blocked_extras.append(key)
            else:
                pure_extras[key] = val

        # Convert Koji data to Tag fields
        return cls(
            koji_id=data['id'],
            name=data['name'],
            locked=data.get('locked', False),
            permission=data.get('perm'),
            arches=split_arches(data.get('arches')),
            maven_support=data.get('maven_support', False),
            maven_include_all=data.get('maven_include_all', False),
            extras=pure_extras,
            block_extras=blocked_extras,
        )


    def set_koji_packages(self, result: VirtualPromise):
        self.packages = [
            PackageEntry(
                name=package['package_name'],
                block=package['blocked'],
                owner=package['owner_name'],
                extra_arches=split_arches(package['extra_arches']))
            for package in result.result]


    def set_koji_groups(self, result: VirtualPromise):
        groups = {}

        for group in result.result:
            pkgs = [TagGroupPackage(
                        name=package['package'],
                        block=package['blocked'])
                    for package in group['packagelist']
                    if package.get('tag_id') == self.koji_id]

            if group.get('tag_id') != self.koji_id and not pkgs:
                # omit empty groups that are not owned by this tag
                continue

            groups[group['name']] = RemoteTagGroup(
                # koji_id=group['group_id'],
                name=group['name'],
                description=group['description'],
                block=group['blocked'],
                packages=pkgs)

        self.groups = groups


    def set_koji_inheritance(self, result: VirtualPromise):
        inher = []
        for inheritance in result.result:
            link = InheritanceLink(
                name=inheritance['name'],
                priority=inheritance['priority'],
                maxdepth=inheritance['maxdepth'],
                noconfig=inheritance['noconfig'],
                pkgfilter=inheritance['pkg_filter'],
                intransitive=inheritance['intransitive'])
            link._parent_tag_id = inheritance['parent_id']
            inher.append(link)

        self.inheritance = inher


    def set_koji_external_repos(self, result: VirtualPromise):
        self.external_repos = [
            ExternalRepoLink(
                name=repo['external_repo_name'],
                priority=repo['priority'],
                arches=split_arches(repo['arches'], allow_none=True),
                merge_mode=repo['merge_mode'])
            for repo in result.result]


    def load_additional_data(self, session: MultiCallSession):
        # Load additional data like inheritance, external repos, packages, etc.
        # This would require multiple API calls

        promise_call(self.set_koji_packages, session.listPackages, tagID=self.name)

        # workaround, don't set inherit=False
        # https://pagure.io/koji/issues/4503
        # if/when fixed, add a version check
        # XXX: promise_call(self.set_koji_groups, session.getTagGroups, self.name, inherit=False, incl_blocked=True)
        promise_call(self.set_koji_groups, session.getTagGroups, self.name, incl_blocked=True)

        promise_call(self.set_koji_inheritance, session.getInheritanceData, self.name)
        promise_call(self.set_koji_external_repos, session.getTagExternalRepos, tag_info=self.name)


# The end.

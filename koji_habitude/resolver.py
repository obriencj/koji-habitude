"""
koji_habitude.resolver

Resolver for units not defined in a Namespace.

For example a namespace may define a tag which inherits some parent,
but that parent is not defined in the namespace. In order for a Solver
to be able to perform depsolving, it must have some way to identify
that parent tag. Therefore an Resolver creates a simple ReferenceObject
placeholder for that parent tag.

:author: Christopher O'Brien  <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Assisted, Mostly Human


import logging
from dataclasses import dataclass
from typing import (TYPE_CHECKING, Any, ClassVar, Dict, Iterable, List,
                    Optional, Sequence, Tuple, Type, Union, cast)

from koji import (ClientSession, MultiCallNotReady, MultiCallSession,
                  VirtualCall)
from typing_extensions import TypeAlias

from .koji import VirtualPromise, multicall
from .models import (BaseKey, BaseStatus, ChangeReport, CoreModel, CoreObject,
                     Field, PrivateAttr, ResolvableMixin)

if TYPE_CHECKING:
    from .namespace import Namespace


__all__ = (
    'Reference',
    'ReferenceChangeReport',
    'Resolver',
    'ResolverReport',
)


logger = logging.getLogger(__name__)


Resolvable: TypeAlias = Union[CoreObject, 'Reference']


class ReferenceChangeReport(ChangeReport):
    """
    A change report for a Reference object.
    """

    obj: 'Reference'

    # we're hijacking the Processor's read and compare steps in order
    # to perform the existence checks, and feed the boolean back onto
    # the ReferenceObject itself.

    def impl_read(self, session: MultiCallSession) -> None:
        self.obj.load_remote(session)

    def impl_compare(self):
        return ()


class Reference(CoreModel, ResolvableMixin):
    """
    A placeholder for a dependency that is not defined in the Namespace
    """

    typename: ClassVar[str] = 'reference'

    # pydantic v1.10 compatibility for ResolvableMixin
    _remote: Optional[VirtualCall] = PrivateAttr(default=None)


    tp: Type[CoreObject] = Field(alias='tp')


    def __init__(self, tp: Type[CoreObject], key: BaseKey):
        typename, name = key
        super().__init__(type=typename, name=name, tp=tp)


    def can_split(self) -> bool:
        return False


    def split(self) -> 'Reference':
        raise TypeError("References cannot be split")


    @property
    def status(self) -> BaseStatus:
        return BaseStatus.DISCOVERED if self.remote() else BaseStatus.PHANTOM


    def is_phantom(self) -> bool:
        return self.remote() is None


    def load_remote(self, session: MultiCallSession, reload: bool = False) -> VirtualCall:
        if reload or self._remote is None:
            self._remote = self.tp.query_remote(session, self.key())
        return self._remote


    def change_report(self, resolver: 'Resolver') -> ReferenceChangeReport:
        return ReferenceChangeReport(self, resolver)


@dataclass
class ResolverReport:
    """
    A snapshot of the phantom and discovered objects in a Resolver, as
    returned by `Resolver.report()`

    The `phantom` dict represents references that *have not* been
    found to exist in a Koji instance. The `discovered` dict represents
    references that *have* been found to exist in a Koji instance.
    """

    discovered: Dict[BaseKey, Resolvable]
    phantoms: Dict[BaseKey, Resolvable]


class Resolver:
    """
    A Resolver finds dependency objects from a Namespace, or provides
    placeholder References for those that do not exist in that Namespace.
    """

    def __init__(self, namespace: 'Namespace'):
        if namespace is None:
            raise ValueError("namespace is required")

        self.namespace: 'Namespace' = namespace
        self._references: Dict[BaseKey, Resolvable] = {}


    def namespace_keys(self) -> Iterable[BaseKey]:
        """
        Iterator over the keys of the objects in the namespace.
        """

        return self.namespace.keys()


    def reference_keys(
            self,
            exists: Optional[bool] = None) -> List[BaseKey]:
        """
        Snapshot of the keys of objects not defined in the
        namespace, but which have been requested via the `resolve`
        method.

        If `exists` is True, filter to only include objects which have
        been found (so far) to exist in a Koji instance.

        If `exists` is False, filter to only include objects which
        have not been found to exist in the Koji instance.

        Reference objects typically determine whether they exist or not
        via the invocation of their `check_exists` method, which is
        part of the Processor's `read` and `compare` steps.
        """

        if exists is None:
            return list(self._references.keys())
        elif exists:
            return [key for key, obj in self._references.items()
                    if obj.remote()]
        else:
            return [key for key, obj in self._references.items()
                    if not obj.remote()]


    def phantom_keys(self) -> List[BaseKey]:
        """
        Iterator of reference keys that are currently phantom (ie. have not yet been
        found to exist in a Koji instance).

        This is a convenience shortcut for `reference_keys(exists=False)`
        """

        return self.reference_keys(exists=False)


    def resolve(self, key: BaseKey) -> Resolvable:
        """
        Resolve a key into either an object from the Namespace, or a
        ReferenceObject placeholder.
        """

        obj = self.namespace.get(key) or self._references.get(key)
        if obj is None:
            tp = cast(Type[CoreObject], self.namespace.get_type(key[0], False))
            if tp is None:
                raise ValueError(f"Unknown type: {key[0]}")
            obj = self._references[key] = Reference(tp, key)
        return obj


    def chain_resolve(self, key, into=None) -> Dict[BaseKey, Resolvable]:
        """
        Resolve a key into either an object from the Namespace, or
        a Reference placeholder. If that object has dependencies,
        resolve them recursively as well.

        :param key: The key to resolve
        :param into: The dictionary to store the resolved objects
        :returns: A dictionary of all resolved objects by their keys
        """

        into = into if into is not None else {}

        obj = self.resolve(key)
        into[key] = obj

        for depkey in obj.dependency_keys():
            if depkey not in into:
                self.chain_resolve(depkey, into)

        return into


    def clear(self) -> None:
        """
        Clear the internal cache of missing objects. Any attempt to
        resolve a missing object will result in a new ReferenceObject
        placeholder being created.
        """

        self._references.clear()


    def load_remote_references(self, session: ClientSession, full=False) -> None:
        """
        creates a multicall for session, and queries for the existence of all
        current reference objects.
        """

        if not self._references:
            return

        with multicall(session) as mc:
            for ref in self._references.values():
                ref.load_remote(mc)

        if not full:
            return

        with multicall(session) as mc:
            for ref in self._references.values():
                remote = ref.remote()
                if remote:
                    remote.load_additional_data(mc)


    def report(self) -> ResolverReport:
        """
        Creates a ResolverReport containing a snapshot of the current references

        :returns: the newly created report
        """

        discovered = {}
        phantoms = {}
        for key, obj in self._references.items():
            if obj.remote():
                discovered[key] = obj
            else:
                phantoms[key] = obj
        return ResolverReport(discovered=discovered, phantoms=phantoms)


# The end.

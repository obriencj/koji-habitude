"""
koji_habitude.resolver

Resolver for units not defined in a Namespace.

For example a namespace may define a tag which inherits some parent,
but that parent is not defined in the namespace. In order for a Solver
to be able to perform depsolving, it must have some way to identify
that parent tag. Therefore an Resolver creates a simple ReferenceObject
placeholder for that parent tag.

Author: Christopher O'Brien  <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Assisted, Mostly Human


from dataclasses import dataclass
import logging
from typing import (
    Any,
    ClassVar,
    Dict,
    Iterator,
    Optional,
    Sequence,
    TYPE_CHECKING,
    Tuple,
    Type,
)

from koji import ClientSession, MultiCallSession, VirtualCall

from .koji import multicall
from .models import Base, BaseKey, BaseStatus, ChangeReport


if TYPE_CHECKING:
    from .namespace import Namespace


__all__ = (
    'Reference',
    'ReferenceChangeReport',
    'Resolver',
    'ResolverReport',
)


logger = logging.getLogger(__name__)


class ReferenceChangeReport(ChangeReport):
    """
    A change report for a Reference object.
    """

    # we're hijacking the Processor's read and compare steps in order
    # to perform the existence checks, and feed the boolean back onto
    # the ReferenceObject itself.

    def impl_read(self, session: MultiCallSession) -> None:
        if self.obj._exists is not None:
            return
        self.obj.query_exists(session)

    def impl_compare(self):
        return ()


class Reference(Base):
    """
    A placeholder for a dependency that is not defined in the Namespace
    """

    typename: ClassVar[str] = 'reference'


    def __init__(self, tp: Type[Base], key: BaseKey):
        self.tp = tp
        self.yaml_type, self.name = key
        self._key = key
        self._exists = None  # None means not checked yet
        logger.debug(f"Reference created: {self.key()}")


    @property
    def status(self) -> BaseStatus:
        return BaseStatus.DISCOVERED if self.exists() else BaseStatus.PHANTOM

    def exists(self) -> Any:
        return self._exists.result if self._exists is not None else None

    def key(self) -> BaseKey:
        return self._key

    def filepos(self) -> Tuple[Optional[str], Optional[int]]:
        return None, None

    def can_split(self) -> bool:
        return False

    def split(self) -> Base:
        raise TypeError("Cannot split a Reference")

    def dependency_keys(self) -> Sequence[BaseKey]:
        return ()

    def change_report(self, resolver: 'Resolver') -> ReferenceChangeReport:
        logger.debug(f"Reference change_report: {self.key()}")
        return ReferenceChangeReport(self, resolver)

    def query_exists(self, session: ClientSession) -> VirtualCall:
        res = self.tp.check_exists(session, self.key())
        if isinstance(res, VirtualCall):
            self._exists = res
        else:
            self._exists = VirtualCall(None, None, None)
            self._exists._result = res
        return self._exists

    @classmethod
    def check_exists(cls, session: ClientSession, key: BaseKey) -> Any:
        msg = ("Reference.check_exists shouldn't be called,"
               " use query_exists instead")
        raise NotImplementedError(msg)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Reference':
        raise TypeError("Reference cannot be created from a dictionary")

    def to_dict(self) -> Dict[str, Any]:
        raise TypeError("Reference cannot be converted to a dictionary")


@dataclass
class ResolverReport:
    """
    A snapshot of the phantom and discovered objects in a Resolver, as
    returned by `Resolver.report()`

    The `phantom` dict represents references that *have not* been
    found to exist in a Koji instance. The `discovered` dict represents
    references that *have* been found to exist in a Koji instance.
    """

    discovered: Dict[BaseKey, Base]
    phantoms: Dict[BaseKey, Base]


class Resolver:
    """
    A Resolver finds dependency objects from a Namespace, or provides
    placeholder References for those that do not exist in that Namespace.
    """

    def __init__(self, namespace: 'Namespace'):
        if namespace is None:
            raise ValueError("namespace is required")

        self.namespace: 'Namespace' = namespace
        self._references: Dict[BaseKey, Base] = {}


    def namespace_keys(self) -> Iterator[BaseKey]:
        """
        Iterator over the keys of the objects in the namespace.
        """

        return self.namespace.keys()


    def reference_keys(
            self,
            exists: Optional[bool] = None) -> Sequence[BaseKey]:
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
                    if obj.exists()]
        else:
            return [key for key, obj in self._references.items()
                    if not obj.exists()]


    def phantom_keys(self) -> Sequence[BaseKey]:
        """
        Iterator of reference keys that are currently phantom (ie. have not yet been
        found to exist in a Koji instance).

        This is a convenience shortcut for `reference_keys(exists=False)`
        """

        return self.reference_keys(exists=False)


    def resolve(self, key: BaseKey) -> Base:
        """
        Resolve a key into either an object from the Namespace, or a
        ReferenceObject placeholder.
        """

        obj = self.namespace.get(key) or self._references.get(key)
        if obj is None:
            tp = self.namespace.get_type(key[0], False)
            obj = self._references[key] = Reference(tp, key)
        return obj


    def chain_resolve(self, key, into=None) -> Dict[BaseKey, Base]:
        """
        Resolve a key into either an object from the Namespace, or
        a Reference placeholder. If that object has dependencies,
        resolve them recursively as well.

        Returns a dictionary of all resolved objects by their keys.
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


    def can_split_key(self, key: BaseKey) -> bool:
        """
        Convenience shortcut for `resolve(key).can_split()`
        """

        return self.resolve(key).can_split()


    def split_key(self, key: BaseKey) -> Base:
        """
        Convenience shortcut for `resolve(key).split()`
        """

        return self.resolve(key).split()


    def query_exists_key(self, session: ClientSession, key: BaseKey) -> VirtualCall:
        """
        Convenience shortcut for `resolve(key).check_exists(session)`
        """

        return self.resolve(key).query_exists(session)


    def query_exists_references(self, session: ClientSession) -> None:
        """
        creates a multicall for session, and queries for the existence of all
        current reference objects.
        """

        if not self._references:
            return

        with multicall(session) as mc:
            for key in self._references.keys():
                self.query_exists_key(mc, key)


    def report(self) -> ResolverReport:
        """
        Return a ResolverReport containing a snapshot of the current references
        """

        discovered = {}
        phantoms = {}
        for key, obj in self._references.items():
            if obj.exists():
                discovered[key] = obj
            else:
                phantoms[key] = obj
        return ResolverReport(discovered=discovered, phantoms=phantoms)


# The end.

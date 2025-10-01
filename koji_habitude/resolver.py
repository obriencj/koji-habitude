"""
koji_habitude.resolver

Resolver for units not defined in a Namespace.

For example a namespace may define a tag which inherits some parent, but that
parent is not defined in the namespace. In order for a Solver to be able to
perform depsolving, it must have some way to identify that parent tag. Therefore
an Resolver creates a simple MissingObject placeholder for that parent tag.

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

from .models import Base, BaseKey, ChangeReport


if TYPE_CHECKING:
    from .namespace import Namespace
    from .resolver import Resolver


__all__ = (
    'MissingChangeReport',
    'MissingObject',
    'Report',
    'Resolver',
)


logger = logging.getLogger(__name__)


class MissingChangeReport(ChangeReport):
    """
    A change report for a missing object.
    """

    # we're hijacking the Processor's read and compare steps in order to perform
    # the existence checks, and feed the boolean back onto the MissingObject
    # itself.

    def impl_read(self, session: MultiCallSession) -> None:
        if self.obj._exists is not None:
            return
        self.obj.query_exists(session)

    def impl_compare(self):
        return ()


class MissingObject(Base):
    """
    A placeholder for a dependency that should exist.
    """

    typename: ClassVar[str] = 'missing'

    def __init__(self, tp: Type[Base], key: BaseKey):
        self.tp = tp
        self.yaml_type, self.name = key
        self._key = key
        self._exists = None  # None means not checked yet
        logger.debug(f"MissingObject created: {self.key()}")


    def exists(self) -> Any:
        return self._exists.result if self._exists is not None else None

    def key(self) -> BaseKey:
        return self._key

    def filepos(self) -> Tuple[Optional[str], Optional[int]]:
        return None, None

    def can_split(self) -> bool:
        return False

    def split(self) -> Base:
        raise TypeError("Cannot split a MissingObject")

    def dependency_keys(self) -> Sequence[BaseKey]:
        return ()

    def change_report(self, resolver: 'Resolver') -> MissingChangeReport:
        logger.debug(f"MissingObject change_report: {self.key()}")
        return MissingChangeReport(self, resolver)

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
        raise NotImplementedError("MissingObject.check_exists shouldn't be called, use query_exists instead")


@dataclass
class Report:
    """
    A snapshot of the missing and found objects in a Resolver, as returned by
    `Resolver.report()`

    The `missing` dict represents MissingObjects that *have not* been found to
    exist in a Koji instance. The `found` dict represents MissingObjects that
    *have* been found to exist in a Koji instance.
    """

    missing: Dict[BaseKey, Base]
    found: Dict[BaseKey, Base]


class Resolver:
    """
    A Resolver finds a dependency object from a Namespace, or provides a
    placeholder for one if it does not exist in that Namespace.
    """

    def __init__(self, namespace: 'Namespace'):
        if namespace is None:
            raise ValueError("namespace is required")

        self.namespace: 'Namespace' = namespace
        self._missing: Dict[BaseKey, Base] = {}


    def namespace_keys(self) -> Iterator[BaseKey]:
        """
        Iterator over the keys of the objects in the namespace.
        """

        return self.namespace.keys()


    def missing_keys(self, exists: Optional[bool] = None) -> Iterator[BaseKey]:
        """
        Snapshot of the keys of objects not defined in the namespace, but which have
        been requested via the `resolve` method.

        If `exists` is True, filter to only include objects which have been
        found (so far) to exist in a Koji instance.

        If `exists` is False, filter to only include objects which have not been
        found to exist in the Koji instance.

        Missing objects typically determine whether they exist or not via the
        invocation of their `check_exists` method, which is part of the Processor's
        `read` and `compare` steps.
        """

        if exists is None:
            return iter(self._missing.keys())
        elif exists:
            return iter([key for key, obj in self._missing.items() if obj.exists()])
        else:
            return iter([key for key, obj in self._missing.items() if not obj.exists()])


    def resolve(self, key: BaseKey) -> Base:
        """
        Resolve a key into either an object from the Namespace, or a
        MissingObject placeholder.
        """

        obj = self.namespace.get(key) or self._missing.get(key)
        if obj is None:
            tp = self.namespace.get_type(key[0], True)
            obj = self._missing[key] = MissingObject(tp, key)
        return obj


    def chain_resolve(self, key, into=None) -> Dict[BaseKey, Base]:
        """
        Resolve a key into either an object from the Namespace, or a
        MissingObject placeholder. If that object has dependencies, resolve them
        recursively as well.

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
        Clear the internal cache of missing objects. Any attempt to resolve a
        missing object will result in a new MissingObject placeholder being
        created.
        """

        self._missing.clear()


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


    def report(self) -> Report:
        """
        Return a Report containing a snapshot of the current missing objects.
        """

        missing = {}
        found = {}
        for key, obj in self._missing.items():
            if obj.exists():
                found[key] = obj
            else:
                missing[key] = obj
        return Report(missing=missing, found=found)


# The end.

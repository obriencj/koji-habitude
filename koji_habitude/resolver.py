"""
koji_habitude.resolver

External resolver for dependency units not defined in a Namespace. A Resolver is
used by a Solver to find a dependency object that isn't already defined, or to
create a placeholder for one if it does not exist.

For example a namespace may define a tag which inherits some parent, but that
parent is not defined in the namespace. In order for a Solver to be able to
perform depsolving, it must have some way to identify that parent tag. Therefore
an Resolver creates a simple MissingObject placeholder for that parent tag. A
more complex OnlineResolver may actually query the koji instance to verify that
the parent tag exists, and produce an Exists entry instead.

Author: Christopher O'Brien  <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Assisted, Mostly Human


from dataclasses import dataclass
import logging
from typing import ClassVar, Dict, Optional, Sequence, Tuple, Type, Any, TYPE_CHECKING

from koji import MultiCallSession
from .models import Base, BaseKey, ChangeReport, Change


if TYPE_CHECKING:
    from .namespace import Namespace
    from .resolver import Resolver


logger = logging.getLogger(__name__)


class MissingChangeReport(ChangeReport):
    """
    A change report for a missing object.
    """

    # we're hijacking the Processor's read and compare steps in order to perform
    # the existence checks, and feed the boolean back onto the MissingObject
    # itself.

    def impl_read(self, session: MultiCallSession) -> None:
        logger.debug(f"MissingChangeReport.impl_read: {self.obj.key()}")
        if self.obj._exists is not None:
            logger.debug(f"MissingChangeReport.impl_read: {self.obj.key()} already checked")
            return
        self.obj._exists = self.obj.tp.check_exists(session, self.obj.key())
        logger.debug(f"MissingChangeReport.impl_read: {self.obj.key()} checked: {self.obj._exists}")

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


@dataclass
class Report:
    """
    A Report is a container for a set of missing dependencies.
    """

    missing: Dict[BaseKey, Base]
    found: Dict[BaseKey, Base]


class Resolver:
    """
    A Resolver finds a dependency object, or a placeholder for one if one does
    not exist.
    """

    def __init__(self, namespace: 'Namespace'):
        if namespace is None:
            raise ValueError("namespace is required")

        self.namespace: 'Namespace' = namespace
        self._missing: Dict[BaseKey, Base] = {}


    def resolve(self, key: BaseKey) -> Base:
        obj = self.namespace._ns.get(key) or self._missing.get(key)
        if obj is None:
            tp = self.namespace.get_type(key[0], True)
            obj = self._missing[key] = MissingObject(tp, key)
        return obj


    def chain_resolve(self, key, into=None) -> Dict[BaseKey, Base]:
        into = into if into is not None else {}

        obj = self.resolve(key)
        into[key] = obj

        for depkey in obj.dependency_keys():
            if depkey not in into:
                self.chain_resolve(depkey, into)

        return into


    def clear(self) -> None:
        self._missing.clear()


    def can_split_key(self, key: BaseKey) -> bool:
        return self.can_split(self.resolve(key))


    def can_split(self, obj: Base) -> bool:
        return obj.can_split()


    def split_key(self, key: BaseKey) -> Base:
        return self.split(self.resolve(key))


    def split(self, obj: Base) -> Base:
        # split the dependency into multiple tiers
        return obj.split()


    def report(self) -> Report:
        # The default Offline implementation does nothing
        missing = {}
        found = {}
        for key, obj in self._missing.items():
            if obj.exists():
                found[key] = obj
            else:
                missing[key] = obj
        return Report(missing=missing, found=found)


# The end.

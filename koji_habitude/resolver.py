"""
koji_habitude.resolver

External resolver for dependency units not defined in a Namespace. A Resolver is
used by a Solver to find a dependency object that isn't already defined, or to
create a placeholder for one if it does not exist.

For example a namespace may define a tag which inherits some parent, but that
parent is not defined in the namespace. In order for a Solver to be able to
perform depsolving, it must have some way to identify that parent tag. Therefore
an Resolver creates a simple MissingObject placeholder for that parent tag. A more
complex OnlineResolver may actually query the koji instance to verify that the
parent tag exists, and produce an Exists entry instead.

Author: Christopher O'Brien  <obriencj@gmail.com> License: GNU General Public
License v3 AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Assisted, Mostly Human


from typing import ClassVar, Dict, List, Optional, Sequence, Tuple

from pydantic import BaseModel, Field

from .models import Base, BaseKey
from .namespace import Namespace


class MissingObject:
    """
    A placeholder for a dependency that should exist.
    """

    typename: ClassVar[str] = 'missing'

    def __init__(self, key: BaseKey):
        self.yaml_type, self.name = key
        self._key = key

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


class Report(BaseModel):
    """
    A Report is a container for a set of missing dependencies.
    """

    missing: List[BaseKey] = Field(default_factory=list)


class Resolver:
    """
    A Resolver finds a dependency object, or a placeholder for one if one does
    not exist.
    """

    def __init__(
            self,
            namespace: Namespace):

        self.namespace: Namespace = namespace
        self.created: Dict[BaseKey, Base] = {}


    def resolve(self, key: BaseKey) -> Base:
        if self.namespace is None:
            obj = self.created.get(key)
        else:
            obj = self.created.get(key) or self.namespace._ns.get(key)
        if obj is None:
            obj = self.created[key] = MissingObject(key)
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
        self.created.clear()


    def can_split_key(self, key: BaseKey) -> bool:
        return self.can_split(self.resolve(key))


    def can_split(self, obj: Base) -> bool:
        return obj.can_split()


    def split_key(self, key: BaseKey) -> Base:
        return self.split(self.resolve(key))


    def split(self, obj: Base) -> Base:
        # split the dependency into multiple tiers
        return obj.split()


    def prepare(self) -> None:
        # The default Offline implementation does nothing
        pass


    def report(self) -> Report:
        # The default Offline implementation does nothing
        return Report(missing=list(self.created.keys()))


class OnlineResolver(Resolver):
    """
    An OnlineResolver is a Resolver that checks the koji instance to verify that
    the dependency exists.
    """

    # TODO
    pass


# The end.

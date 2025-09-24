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


from pydantic import BaseModel, Field
from typing import Any, ClassVar, Dict, List, Set, Tuple

from .namespace import Namespace


class MissingObject:
    """
    A placeholder for a dependency that should exist.
    """

    typename: ClassVar[str] = 'missing'

    def __init__(self, key: Tuple[str, str]):
        self.yaml_type, self.name = key
        self._key = key

    def key(self):
        return self._key

    def filepos(self):
        return None, None

    def can_split(self):
        return False

    def split(self):
        return self

    def dependency_keys(self):
        return ()


class Report(BaseModel):
    """
    A Report is a container for a set of missing dependencies.
    """

    missing: List[Tuple[str, str]] = Field(default_factory=list)


class Resolver:
    """
    A Resolver finds a dependency object, or a placeholder for one if one does
    not exist.
    """

    def __init__(
            self,
            namespace: Namespace):

        self.namespace = namespace
        self.created = {}


    def resolve(self, key):
        if self.namespace is None:
            obj = self.created.get(key)
        else:
            obj = self.created.get(key) or self.namespace._ns.get(key)
        if obj is None:
            obj = self.created[key] = MissingObject(key)
        return obj


    def clear(self):
        self.created.clear()


    def can_split_key(self, key):
        return self.can_split(self.resolve(key))


    def can_split(self, obj):
        return obj.can_split()


    def split_key(self, key):
        return self.split(self.resolve(key))


    def split(self, obj):
        # split the dependency into multiple tiers
        return obj.split()


    def prepare(self):
        # The default Offline implementation does nothing
        pass


    def report(self):
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

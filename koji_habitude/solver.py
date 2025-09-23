"""
koji_habitude.dependency

Dependency tree

Author: Christopher O'Brien  <obriencj@gmail.com>
License: GNU General Public License v3
"""

# Vibe-Coding State: AI Assisted, Mostly Human

# special call-out to the Claude AI on this one. I wrote most of this by hand,
# but had an ongoing discussion regarding the design of the solver. The
# back-and-forth discussion was extremely helpful, even if the AI never actually
# emitted code.


from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Tuple

from .models import Base
from .namespace import Namespace


class MissingObject(Base):
    """
    A placeholder for a dependency that should exist.
    """

    typename = 'missing'

    def __init__(self, key: Tuple[str, str]):
        self.typename, self.name = key
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


@dataclass
class Report:
    """
    A Report is a container for a set of missing dependencies.
    """

    missing: List[Tuple[str, str]] = field(default_factory=list)


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
        return Report(missing=self.created.keys())


class OnlineResolver(Resolver):
    """
    An OnlineResolver is a Resolver that checks the koji instance to verify that
    the dependency exists.
    """

    # TODO
    pass


class Node:
    def __init__(self, obj, splitable=False):
        self.key = obj.key()
        self.obj = obj
        self.can_split = splitable
        self.dependencies = {}
        self.dependents = {}

    def add_dependency(self, node):
        self.dependencies[node.key] = node
        node.dependents[self.key] = self

    def unlink(self):
        key = self.key
        for depnode in self.dependents.values():
            depnode.dependencies.pop(key)
        for depnode in self.dependencies.values():
            depnode.dependents.pop(key)
        self.dependencies.clear()
        self.dependents.clear()

    @property
    def score(self):
        return len(self.dependencies)

    def get_priority(self):
        return (len(self.dependencies),
                0 if self.can_split else 1,
                0 - len(self.dependents))


class Solver:

    """
    A Solver is a container for a set of nodes that have been resolved to a
    particular tier. It is used to iterate over the nodes in the tier, and to
    create a new tier by resolving the dependents of the nodes.
    """


    def __init__(
        self,
        resolver: Resolver,
        work: List[Tuple[str, str]]):

        self.resolver = resolver
        self.work = work
        self.remaining = None


    def remaining_keys(self):
        if self.remaining is None:
            raise ValueError("Solver not prepared")
        return set(self.remaining.keys())


    def prepare(self):
        if self.remaining is not None:
            raise ValueError("Solver already prepared")

        # create Node for every key in work, wrapping the resolver.resolve()
        self.remaining = {key: Node(self.resolver.resolve(key)) for key in self.work}

        for node in self.remaining.values():
            for depkey in node.obj.dependency_keys():
                depnode = self.remaining.get(depkey)
                if depnode is None:
                    depnode = Node(self.resolver.resolve(depkey))
                    self.remaining[depkey] = depnode
                node.add_dependency(depnode)

        # allows resolver to process any items it needed to create
        return self.resolver.prepare()


    def report(self):
        return self.resolver.report()


    def _unlink(self, node):
        self.remaining.pop(node.key)
        node.unlink()
        return node.obj


    def _split(self, node):
        splitnode = Node(self.resolver.split(node.obj), splitable=False)

        # steal the dependents from the original node and put them on the split
        # node
        splitnode.dependents = node.dependents
        node.dependents = {}

        key = node.key
        for dependent in splitnode.dependents.values():
            dependent.dependencies.pop(key)

            # this isn't really necessary, since we'll be unlinking it shortly
            # after being created, but may as well.
            dependent.add_dependency(splitnode)

        return splitnode


    def __iter__(self):
        # create a list of nodes, sorted by priority

        work = sorted(self.remaining.values(), key=Node.get_priority)
        acted = False

        while work:
            # get an iterator over the work list
            for node in work:
                if node.score == 0:
                    yield self._unlink(node)
                    acted = True

                elif node.can_split:
                    yield self._unlink(self._split(node))
                    acted = True
                    if node.score == 0:
                        yield self._unlink(node)
                    break

                else:
                    if not acted:
                        raise ValueError("Stuck in a loop")
                    break

            work = sorted(self.remaining.values(), key=Node.get_priority)
            acted = False

        assert len(self.remaining) == 0


# The end.

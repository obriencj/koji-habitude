"""
koji_habitude.solver

Dependency resolution order solver

Author: Christopher O'Brien  <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Assisted, Mostly Human

# special call-out to the Claude AI on this one. I wrote most of this by hand,
# but had an ongoing discussion regarding the design of the solver. The
# back-and-forth discussion was extremely helpful, even if the AI never actually
# emitted code.


from typing import List, Tuple, Optional

from .resolver import Resolver


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
    A Solver is a container for a set of nodes, iterated over in a dependency
    solved order. It can optionally accept a list of work keys to use as a
    limited starting point for depsolving from the namespace, in which case it
    will only solve for those keys and their dependencies.
    """

    def __init__(
        self,
        resolver: Resolver,
        work: Optional[List[Tuple[str, str]]] = None):

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

        into = {}

        if self.work is None:
            for key in self.resolver.namespace._ns:
                self.resolver.chain_resolve(key, into)
        else:
            for key in self.work:
                self.resolver.chain_resolve(key, into)

        self.remaining = {key: Node(obj) for key, obj in into.items()}
        for node in self.remaining.values():
            for depkey in node.obj.dependency_keys():
                depnode = self.remaining.get(depkey)
                assert depnode is not None
                node.add_dependency(depnode)

        # allows resolver to process any items it needed to create
        return self.resolver.prepare()


    def report(self):
        if self.remaining is None:
            raise ValueError("Solver not prepared")
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

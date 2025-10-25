"""
koji_habitude.solver

Dependency resolution order solver

:author: Christopher O'Brien  <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Assisted, Mostly Human

# special call-out to the Claude AI on this one. I wrote most of this
# by hand, but had an ongoing discussion regarding the design of the
# solver. The back-and-forth discussion was extremely helpful, even if
# the AI never actually emitted code.


from typing import TYPE_CHECKING, Dict, Iterator, List, Optional, Set, Tuple, Union
from typing_extensions import TypeAlias

from .models import BaseKey, CoreObject

if TYPE_CHECKING:
    from .resolver import Resolver, ResolverReport, Reference


Solvable: TypeAlias = Union[CoreObject, 'Reference']


class Node:
    """
    Represents a node in the dependency graph, wrapping a Base object of some
    type. Used internally by the Solver to track dependency links.
    """

    def __init__(self, obj: Solvable, splitable: bool = None):
        self.key: BaseKey = obj.key()
        self.obj: Solvable = obj

        if splitable is None:
            self.can_split: bool = obj.can_split()
        else:
            self.can_split = splitable

        self.dependencies: Dict[BaseKey, 'Node'] = {}
        self.dependents: Dict[BaseKey, 'Node'] = {}


    def add_dependency(self, node: 'Node') -> None:
        self.dependencies[node.key] = node
        node.dependents[self.key] = self


    def unlink(self) -> None:
        key = self.key
        for depnode in self.dependents.values():
            depnode.dependencies.pop(key)
        for depnode in self.dependencies.values():
            depnode.dependents.pop(key)
        self.dependencies.clear()
        self.dependents.clear()


    @property
    def score(self) -> int:
        return len(self.dependencies)


    def get_priority(self) -> Tuple[bool, bool, int]:
        return (bool(self.dependencies),
                not self.can_split,
                0 - len(self.dependents))


    def __repr__(self):
        return f"<Node(key={self.key}, priority={self.get_priority()})>"


class Solver:
    """
    A Solver is a container for a set of nodes, iterated over in a
    dependency solved order. It can optionally accept a list of work
    keys to use as a limited starting point for depsolving from the
    namespace, in which case it will only solve for those keys and
    their dependencies.
    """

    def __init__(
            self,
            resolver: 'Resolver',
            work: Optional[List[BaseKey]] = None):

        self.resolver: 'Resolver' = resolver
        self.work: Optional[List[BaseKey]] = work
        self.remaining: Optional[Dict[BaseKey, Node]] = None


    def remaining_keys(self) -> Set[BaseKey]:
        if self.remaining is None:
            raise ValueError("Solver not prepared")
        return set(self.remaining.keys())


    def prepare(self) -> None:
        if self.remaining is not None:
            raise ValueError("Solver already prepared")

        into: Dict[BaseKey, Solvable] = {}

        if self.work is None:
            for key in self.resolver.namespace_keys():
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


    def report(self) -> 'ResolverReport':
        if self.remaining is None:
            raise ValueError("Solver not prepared")
        return self.resolver.report()


    def _unlink(self, node: Node) -> Solvable:
        self.remaining.pop(node.key)
        node.unlink()
        return node.obj


    def _split(self, node: Node) -> Solvable:
        key = node.key
        for dependent in node.dependents.values():
            dependent.dependencies.pop(key)
        node.dependents.clear()

        return node.obj.split()


    def __iter__(self) -> Iterator[Solvable]:
        # create a list of nodes, sorted by priority

        acted: bool = False
        work: List[Node] = sorted(self.remaining.values(),
                                  key=Node.get_priority)

        while work:
            for node in work:
                if node.score == 0:
                    yield self._unlink(node)
                    acted = True

                elif acted:
                    break

                elif node.can_split:
                    yield self._split(node)
                    acted = True
                    break

                else:
                    raise ValueError("Stuck in a loop")

            acted = False
            work = sorted(self.remaining.values(),
                          key=Node.get_priority)

        assert len(self.remaining) == 0


# The end.

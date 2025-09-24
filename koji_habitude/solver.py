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


from typing import Dict, Iterator, List, Optional, Set, Tuple

from .models import Base, BaseKey
from .resolver import Report, Resolver


class Node:
    def __init__(self, obj: Base, splitable: bool = None):
        self.key: BaseKey = obj.key()
        self.obj: Base = obj
        self.can_split: bool = splitable if splitable is not None else obj.can_split()
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

    def get_priority(self) -> Tuple[int, int, int]:
        return (len(self.dependencies),
                0 if self.can_split else 1,
                0 - len(self.dependents))

    def __repr__(self):
        return f"<Node(key={self.key}, priority={self.get_priority()})>"


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
        work: Optional[List[BaseKey]] = None):

        self.resolver: Resolver = resolver
        self.work: Optional[List[BaseKey]] = work
        self.remaining: Optional[Dict[BaseKey, Node]] = None


    def remaining_keys(self) -> Set[BaseKey]:
        if self.remaining is None:
            raise ValueError("Solver not prepared")
        return set(self.remaining.keys())


    def prepare(self) -> None:
        if self.remaining is not None:
            raise ValueError("Solver already prepared")

        into: Dict[BaseKey, Base] = {}

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


    def report(self) -> Report:
        if self.remaining is None:
            raise ValueError("Solver not prepared")
        return self.resolver.report()


    def _unlink(self, node: Node) -> Base:
        self.remaining.pop(node.key)
        node.unlink()
        return node.obj


    def _split(self, node: Node) -> Base:
        key = node.key
        for dependent in node.dependents.values():
            dependent.dependencies.pop(key)
        node.dependents.clear()

        return self.resolver.split(node.obj)


    def __iter__(self) -> Iterator[Base]:
        # create a list of nodes, sorted by priority

        work: List[Node] = sorted(self.remaining.values(), key=Node.get_priority)
        acted: bool = False

        while work:
            # print(f"Work: {work}")
            # get an iterator over the work list
            for node in work:
                # print(f"Node: {node.key}, Score: {node.score}, Can Split: {node.can_split}")
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

            work = sorted(self.remaining.values(), key=Node.get_priority)
            acted = False

        assert len(self.remaining) == 0


# The end.

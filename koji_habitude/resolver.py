"""
koji-habitude - resolver

Dependency resolution and tiered execution logic for koji objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""


from typing import List, Optional, Set, Tuple, Dict, TYPE_CHECKING
from collections import defaultdict

if TYPE_CHECKING:
    from .models.base import BaseKojiObject
    from .object_map import ObjectMap


class ObjectTier:
    """
    Represents a tier of objects that can be processed together.
    """

    def __init__(self, objects: List['BaseKojiObject']):
        """
        Initialize object tier.

        Args:
            objects: List of objects at this tier level
        """

        self.objects = objects

    def __iter__(self):
        """
        Iterate over objects in this tier.
        """

        return iter(self.objects)

    def __len__(self) -> int:
        """
        Return number of objects in this tier.
        """

        return len(self.objects)

    def __bool__(self) -> bool:
        """
        Return True if tier has objects.
        """

        return bool(self.objects)

    def next_tier(self, obj_map: 'ObjectMap') -> Optional['ObjectTier']:
        """
        Create the next tier from objects that depend on this tier.

        Args:
            obj_map: ObjectMap to resolve dependents from

        Returns:
            Next ObjectTier or None if no more tiers
        """

        next_objects = []
        processed_keys = set()

        # Collect all objects that depend on objects in this tier
        for obj in self.objects:
            dependents = obj_map.get_dependents(obj.key)
            for dependent in dependents:
                if dependent.key not in processed_keys:
                    next_objects.append(dependent)
                    processed_keys.add(dependent.key)

        if not next_objects:
            return None

        # Resolve cross-dependencies in the next tier
        resolved_tier = resolve_cross_dependencies(next_objects, obj_map)
        return resolved_tier


def resolve_leaves(obj_map: 'ObjectMap') -> ObjectTier:
    """
    Find objects with no dependents to create the first tier.

    Args:
        obj_map: ObjectMap to analyze

    Returns:
        ObjectTier containing leaf objects
    """

    leaf_objects = obj_map.get_objects_with_no_dependents()
    return ObjectTier(leaf_objects)


def resolve_cross_dependencies(objects: List['BaseKojiObject'], obj_map: 'ObjectMap') -> ObjectTier:
    """
    Resolve cross-dependencies within a tier using deferral.

    When objects in the same tier depend on each other, we create deferred
    versions that can be processed in a later tier.

    Args:
        objects: List of objects that may have cross-dependencies
        obj_map: ObjectMap for dependency resolution

    Returns:
        ObjectTier with cross-dependencies resolved via deferral
    """

    if not objects:
        return ObjectTier([])

    # Build dependency graph within this tier
    tier_keys = {obj.key for obj in objects}
    cross_deps = defaultdict(list)

    for obj in objects:
        for dep_key in obj.dependent_keys():
            if dep_key in tier_keys:
                cross_deps[obj.key].append(dep_key)

    # If no cross-dependencies, return as-is
    if not cross_deps:
        return ObjectTier(objects)

    # Resolve cross-dependencies using deferral
    resolved_objects = []
    deferred_objects = []

    for obj in objects:
        obj_cross_deps = cross_deps.get(obj.key, [])

        if obj_cross_deps:
            # Create deferred version of this object
            deferred_obj = obj.defer_deps(obj_cross_deps)
            resolved_objects.append(deferred_obj)

            # Create deferred dependency object for later processing
            deferred_data = obj.data.copy()
            deferred_data['type'] = f"deferred_{obj.type}"

            # Import here to avoid circular import
            from .models.base import BaseKojiObject

            class DeferredObject(BaseKojiObject):
                """
                Wrapper for deferred object data.
                """

                def dependent_keys(self) -> List[Tuple[str, str]]:
                    """
                    Return deferred dependencies.
                    """

                    # Deferred objects depend on the original cross-dependencies
                    return obj_cross_deps

            deferred_wrapper = DeferredObject(deferred_data)
            deferred_objects.append(deferred_wrapper)

        else:
            # No cross-dependencies, use object as-is
            resolved_objects.append(obj)

    # Add deferred objects to the object map for later processing
    for deferred_obj in deferred_objects:
        obj_map.add_object(deferred_obj)

    return ObjectTier(resolved_objects)


def build_dependency_graph(obj_map: 'ObjectMap') -> Dict[Tuple[str, str], Set[Tuple[str, str]]]:
    """
    Build a complete dependency graph for all objects.

    Args:
        obj_map: ObjectMap to analyze

    Returns:
        Dictionary mapping object keys to their dependency keys
    """

    graph = {}

    for obj_key, obj in obj_map.items():
        deps = set(obj.dependent_keys())
        graph[obj_key] = deps

    return graph


def detect_circular_dependencies(obj_map: 'ObjectMap') -> List[List[Tuple[str, str]]]:
    """
    Detect circular dependencies in the object map.

    Args:
        obj_map: ObjectMap to analyze

    Returns:
        List of circular dependency chains found
    """

    graph = build_dependency_graph(obj_map)
    visited = set()
    rec_stack = set()
    cycles = []

    def dfs_cycle_detect(node: Tuple[str, str], path: List[Tuple[str, str]]) -> None:
        """
        Depth-first search to detect cycles.
        """

        if node in rec_stack:
            # Found a cycle
            cycle_start = path.index(node)
            cycle = path[cycle_start:] + [node]
            cycles.append(cycle)
            return

        if node in visited:
            return

        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for dep in graph.get(node, set()):
            if dep in graph:  # Only follow dependencies that exist in our graph
                dfs_cycle_detect(dep, path)

        rec_stack.remove(node)
        path.pop()

    # Check each object for cycles
    for obj_key in graph:
        if obj_key not in visited:
            dfs_cycle_detect(obj_key, [])

    return cycles


def resolve_tiers(obj_map: 'ObjectMap') -> List[ObjectTier]:
    """
    Resolve all tiers for the given object map.

    Args:
        obj_map: ObjectMap to resolve into tiers

    Returns:
        List of ObjectTiers in dependency order
    """

    tiers = []
    current_tier = resolve_leaves(obj_map)

    while current_tier:
        tiers.append(current_tier)
        current_tier = current_tier.next_tier(obj_map)

    return tiers

# The end.

"""
koji-habitude - object_map

Object mapping and dependency tracking for koji objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

from typing import Dict, List, Tuple, Optional, Any, Set, TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from .models.base import BaseKojiObject


class Resolver(ABC):
    """
    Abstract base class for dependency resolvers.
    """
    
    @abstractmethod
    def resolve_object(self, key: Tuple[str, str]) -> Optional['BaseKojiObject']:
        """
        Attempt to resolve a missing object dependency.
        
        Args:
            key: (type, name) tuple identifying the object
            
        Returns:
            Resolved object or None if not found
        """
        
        pass


class OnlineResolver(Resolver):
    """
    Resolver that checks koji instance for missing dependencies.
    """
    
    def __init__(self, koji_profile: Optional[str] = None):
        """
        Initialize online resolver.
        
        Args:
            koji_profile: Koji profile to use for connections
        """
        
        self.koji_profile = koji_profile
        
    def resolve_object(self, key: Tuple[str, str]) -> Optional['BaseKojiObject']:
        """
        Check koji instance for the missing object.
        
        TODO: Implement koji instance lookup
        
        Args:
            key: (type, name) tuple identifying the object
            
        Returns:
            Object if found in koji, None otherwise
        """
        
        # TODO: Query koji instance to verify object exists
        # For now, just return None to indicate not found locally
        return None


class OfflineResolver(Resolver):
    """
    Resolver that records missing dependencies for warnings.
    """
    
    def __init__(self):
        """
        Initialize offline resolver.
        """
        
        self.missing_objects: Set[Tuple[str, str]] = set()
        
    def resolve_object(self, key: Tuple[str, str]) -> Optional['BaseKojiObject']:
        """
        Record missing object for warning.
        
        Args:
            key: (type, name) tuple identifying the object
            
        Returns:
            Always None (offline mode)
        """
        
        self.missing_objects.add(key)
        return None
        
    def get_missing_objects(self) -> List[Tuple[str, str]]:
        """
        Get list of all missing objects encountered.
        
        Returns:
            List of (type, name) tuples for missing objects
        """
        
        return list(self.missing_objects)


class ObjectMap:
    """
    Central registry for koji objects with dependency tracking.
    """
    
    def __init__(self, resolver: Resolver):
        """
        Initialize object map.
        
        Args:
            resolver: Resolver to use for missing dependencies
        """
        
        self.objects: Dict[Tuple[str, str], 'BaseKojiObject'] = {}
        self.dependents_map: Dict[Tuple[str, str], List[Tuple[str, str]]] = {}
        self.resolver = resolver
        
    def add_object(self, obj: 'BaseKojiObject') -> None:
        """
        Add object to the map and update dependency tracking.
        
        Args:
            obj: Object to add to the map
        """
        
        self.objects[obj.key] = obj
        
        # Update reverse dependency mapping
        for dep_key in obj.dependent_keys():
            if dep_key not in self.dependents_map:
                self.dependents_map[dep_key] = []
            self.dependents_map[dep_key].append(obj.key)
            
    def get_object(self, key: Tuple[str, str]) -> Optional['BaseKojiObject']:
        """
        Get object by key, falling back to resolver if not found.
        
        Args:
            key: (type, name) tuple identifying the object
            
        Returns:
            Object if found locally or via resolver, None otherwise
        """
        
        # Check local objects first
        if key in self.objects:
            return self.objects[key]
            
        # Fall back to resolver
        resolved = self.resolver.resolve_object(key)
        if resolved:
            # Cache resolved object
            self.objects[key] = resolved
            
        return resolved
        
    def get_objects_with_no_dependents(self) -> List['BaseKojiObject']:
        """
        Find objects that have no other objects depending on them.
        
        These are the "leaf" nodes that can be processed first.
        
        Returns:
            List of objects with no dependents
        """
        
        leaves = []
        
        for obj_key, obj in self.objects.items():
            # Check if this object has any dependents
            if obj_key not in self.dependents_map or not self.dependents_map[obj_key]:
                leaves.append(obj)
                
        return leaves
        
    def get_dependents(self, key: Tuple[str, str]) -> List['BaseKojiObject']:
        """
        Get all objects that depend on the specified object.
        
        Args:
            key: (type, name) tuple identifying the object
            
        Returns:
            List of objects that depend on the specified object
        """
        
        dependent_keys = self.dependents_map.get(key, [])
        dependents = []
        
        for dep_key in dependent_keys:
            obj = self.get_object(dep_key)
            if obj:
                dependents.append(obj)
                
        return dependents
        
    def remove_object(self, key: Tuple[str, str]) -> None:
        """
        Remove object from the map and clean up dependency tracking.
        
        Args:
            key: (type, name) tuple identifying the object to remove
        """
        
        if key in self.objects:
            obj = self.objects[key]
            
            # Clean up reverse dependency mappings
            for dep_key in obj.dependent_keys():
                if dep_key in self.dependents_map:
                    try:
                        self.dependents_map[dep_key].remove(key)
                        if not self.dependents_map[dep_key]:
                            del self.dependents_map[dep_key]
                    except ValueError:
                        pass  # Key wasn't in the list
                        
            # Remove the object itself
            del self.objects[key]
            
            # Remove from dependents map if it exists there
            if key in self.dependents_map:
                del self.dependents_map[key]
                
    def __len__(self) -> int:
        """
        Return number of objects in the map.
        """
        
        return len(self.objects)
        
    def __contains__(self, key: Tuple[str, str]) -> bool:
        """
        Check if object exists in the map.
        """
        
        return key in self.objects
        
    def keys(self):
        """
        Return iterator over object keys.
        """
        
        return self.objects.keys()
        
    def values(self):
        """
        Return iterator over objects.
        """
        
        return self.objects.values()
        
    def items(self):
        """
        Return iterator over (key, object) pairs.
        """
        
        return self.objects.items()

# The end.

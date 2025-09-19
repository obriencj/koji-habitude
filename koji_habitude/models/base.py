"""
koji-habitude - models.base

Base class for all koji object models with dependency tracking.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

from typing import Dict, List, Tuple, Optional, Any, TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from ..object_map import ObjectMap


class BaseKojiObject(ABC):
    """
    Base class for all koji object models.
    """
    
    def __init__(self, data: Dict[str, Any]):
        """
        Initialize koji object from data dictionary.
        
        Args:
            data: Dictionary containing object configuration
        """
        
        self.type = data['type']
        self.name = data['name']
        self.data = data.copy()
        
    @property
    def key(self) -> Tuple[str, str]:
        """
        Return the unique (type, name) identifier for this object.
        """
        
        return (self.type, self.name)
        
    @abstractmethod
    def dependent_keys(self) -> List[Tuple[str, str]]:
        """
        Return list of (type, name) keys this object depends on.
        
        Returns:
            List of dependency keys that must exist before this object
        """
        
        pass
        
    def dependents(self, obj_map: 'ObjectMap') -> List['BaseKojiObject']:
        """
        Resolve dependency objects from the object map.
        
        Args:
            obj_map: ObjectMap to resolve dependencies from
            
        Returns:
            List of resolved dependency objects
        """
        
        deps = []
        for dep_key in self.dependent_keys():
            dep_obj = obj_map.get_object(dep_key)
            if dep_obj:
                deps.append(dep_obj)
        return deps
        
    def defer_deps(self, dep_list: List[Tuple[str, str]]) -> 'BaseKojiObject':
        """
        Create copy with specified dependencies deferred.
        
        This creates a new object instance that removes the problematic
        dependencies and adds a deferred dependency to handle them later.
        
        Args:
            dep_list: List of dependency keys to defer
            
        Returns:
            New object instance with deferred dependencies
        """
        
        # Create a copy of this object's data
        new_data = self.data.copy()
        
        # Remove the problematic dependencies from the copy
        # This is model-specific and should be overridden by subclasses
        deferred_data = self._extract_deferred_data(dep_list)
        
        # Create the main object without the deferred data
        main_obj = self.__class__(new_data)
        
        # The deferred object will be handled by the dependency system
        # It will be created as a ('deferred_' + type, name) object
        return main_obj
        
    def _extract_deferred_data(self, dep_list: List[Tuple[str, str]]) -> Dict[str, Any]:
        """
        Extract data that should be deferred to later tier.
        
        Subclasses should override this to handle model-specific deferral.
        
        Args:
            dep_list: List of dependency keys being deferred
            
        Returns:
            Dictionary of data that was extracted for deferral
        """
        
        return {}
        
    def koji_diff(self, koji_data: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Compare with koji data and return update calls.
        
        TODO: This is left as a stub for future implementation.
        
        Args:
            koji_data: Current state from koji instance, or None if not found
            
        Returns:
            List of koji API calls needed to update the object
        """
        
        # TODO: Implement object diffing logic
        return []
        
    def __repr__(self) -> str:
        """
        String representation of the object.
        """
        
        return f"{self.__class__.__name__}({self.type}, {self.name})"
        
    def __eq__(self, other) -> bool:
        """
        Equality comparison based on key.
        """
        
        if not isinstance(other, BaseKojiObject):
            return False
        return self.key == other.key
        
    def __hash__(self) -> int:
        """
        Hash based on key for use in sets/dicts.
        """
        
        return hash(self.key)

# The end.
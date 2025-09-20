"""
koji-habitude - models.base

Base class for all koji object models with dependency tracking.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated with Human Rework


from typing import Dict, List, Tuple, Optional, Any, TYPE_CHECKING
from abc import ABC, abstractmethod


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

        self.typename = data['type']
        self.name = data['name']
        self.key = (self.typename, self.name)

        self.data = data

        self.dependants = []


    def dependency_keys(self):
        return ()


    def defer_deps(self)) -> 'BaseKojiObject':
        """
        Create a minimal copy of this object specifying only that it needs
        to exist, with a dependant link on the original object.

        This allows us to create cross-dependencies of the same tier without
        any internal references that break ordering. Then the next tier can
        add the links.
        """

        deferal = type(self)({
            "type": self.typename,
            "name": self.name
        })

        deferal.dependants.append(self)
        return deferal


    def koji_diff(
            self,
            koji_data: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:

        """
        Compare with koji data and return update calls.

        TODO: This is left as a stub for future implementation.

        Args:
            koji_data: Current state from koji instance, or None if not found

        Returns:
            List of koji API calls needed to update the object
        """

        # TODO: Implement object diffing logic
        return ()


    def __repr__(self) -> str:
        """
        String representation of the object.
        """

        return f"<{self.__class__.__name__}({self.type}, {self.name})>"


# The end.

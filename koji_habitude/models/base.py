"""
koji_habitude.models.base

Base class for koji object models

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated with Human Rework


from abc import ABC
from typing import Any, Dict, List, Optional, Protocol, Sequence, TYPE_CHECKING, Tuple


class Base(Protocol):
    typename: str

    name: str

    filename: Optional[str]
    lineno: Optional[int]
    trace: Optional[List[Dict[str, Any]]]

    def __init__(self, data: Dict[str, Any]) -> None:
        ...

    def key(self) -> Tuple[str, str]:
        ...

    def filepos(self) -> Tuple[Optional[str], Optional[int]]:
        ...

    def can_split(self) -> bool:
        ...

    def split(self) -> Optional['Base']:
        ...

    def dependency_keys(self) -> Sequence[Tuple[str, str]]:
        ...


class BaseObject(Base):

    typename = 'object'

    def __init__(self, data: Dict[str, Any]) -> None:
        name = data.get('name')
        name = name and name.strip()
        if not name:
            raise ValueError("Non-empty name is required")

        self.name = data['name']
        self.filename = data.get('__file__')
        self.lineno = data.get('__line__')
        self.trace = data.get('__trace__')

    def key(self) -> Tuple[str, str]:
        return (self.typename, self.name)

    def filepos(self) -> Tuple[Optional[str], Optional[int]]:
        return (self.filename, self.lineno)

    def can_split(self):
        return False

    def split(self):
        raise TypeError(f"Cannot split {self.typename}")

    def dependency_keys(self):
        return ()


class RawObject(BaseObject):

    typename = 'raw'

    def __init__(self, data: Dict[str, Any]) -> None:
        super().__init__(data)
        self.data = data
        self.typename = data.get('type', 'raw')


class BaseKojiObject(ABC, BaseObject):
    """
    Base class for all koji object models.
    """

    # override in subclasses
    typename = 'koji-object'

    # override in subclasses to support splitting
    _can_split = False


    def __init__(self, data: Dict[str, Any]) -> None:
        """
        Initialize koji object from data dictionary.

        Args:
            data: Dictionary containing object configuration
        """

        super().__init__(data)
        self.data = data


    def can_split(self):
        return self._can_split


    def split(self) -> 'BaseKojiObject':
        """
        Create a minimal copy of this object specifying only that it needs
        to exist, with a dependant link on the original object.

        This allows us to create cross-dependencies of the same tier without
        any internal references that break ordering. Then the next tier can
        add the links.
        """

        return type(self)({
            "type": self.typename,
            "name": self.name
        })


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

        return f"<{self.__class__.__name__}({self.typename}, {self.name})>"


# The end.

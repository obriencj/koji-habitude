"""
koji_habitude.models.base

Base class for koji object models

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated with Human Rework


from pydantic import BaseModel, Field

from typing import (
    Any, ClassVar, Dict, List, Optional, Protocol,
    Sequence, Tuple,
)


__all__ = (
    'Base',
    'BaseObject',
    'BaseKojiObject',
)


class Base(Protocol):
    typename: str

    name: str

    filename: Optional[str]
    lineno: Optional[int]
    trace: Optional[List[Dict[str, Any]]]

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

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Base':
        ...


class BaseObject(BaseModel):
    """
    Adapter between the Base protocol and Pydantic models.
    """

    typename: ClassVar[str] = 'object'

    name: str = Field(alias='name')
    yaml_type: str = Field(alias='type', default=None)
    filename: Optional[str] = Field(alias='__file__', default=None)
    lineno: Optional[int] = Field(alias='__line__', default=None)
    trace: Optional[List[Dict[str, Any]]] = Field(alias='__trace__', default_factory=list)

    # this is the record of the `from_dict` call if it was used
    _data: Optional[Dict[str, Any]] = None


    def model_post_init(self, __context: Any):
        name = self.name and self.name.strip()
        if not name:
            raise ValueError(f"name is required for {self.typename}")
        self.name = name

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseObject':
        obj = cls.model_validate(data)
        obj._data = data
        return obj

    @property
    def data(self) -> Dict[str, Any] | None:
        """
        Access the raw data that was used if this object was created via `from_dict`
        """
        return self._data

    def key(self) -> Tuple[str, str]:
        return (self.typename, self.name)

    def filepos(self) -> Tuple[Optional[str], Optional[int]]:
        return (self.filename, self.lineno)

    def filepos_str(self) -> str:
        filename = self.filename or '<unknown>'
        if self.lineno:
            return f"{filename}:{self.lineno}"
        else:
            return filename

    def can_split(self):
        return False

    def split(self):
        raise TypeError(f"Cannot split {self.typename}")

    def dependency_keys(self):
        return ()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.typename}, {self.name})>"


class BaseKojiObject(BaseObject):
    """
    Base class for all koji object models.
    """

    # override in subclasses
    typename: ClassVar[str] = 'koji-object'

    # override in subclasses to support splitting
    _can_split: ClassVar[bool] = False


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

        return type(self)(name=self.name)


    def diff(
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


# The end.

"""
koji_habitude.models.base

Base class for koji object models

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated with Human Rework


from enum import Enum
from typing import (TYPE_CHECKING, Any, ClassVar, Dict, List, Optional, Protocol,
                    Sequence, Tuple, Type, TypeVar)

from koji import MultiCallNotReady, MultiCallSession, VirtualCall
from typing_extensions import TypeAlias

from ..koji import PromiseMultiCallSession
from .compat import BaseModel, Field, Mixin, PrivateAttr, field_validator

if TYPE_CHECKING:
    from ..resolver import Resolver
    from .change import ChangeReport


__all__ = (
    'BaseKey',
    'BaseStatus',
    'SubModel',

    # Pydantic mixins
    'IdentifiableMixin',
    'LocalMixin',
    'ResolvableMixin',

    # Base classes for core types
    'CoreModel',
    'CoreObject',
    'RemoteObject',
)


BaseKey: TypeAlias = Tuple[str, str]
"""
A tuple of (typename, name), used as the key for objects across this package
"""


class BaseStatus(Enum):
    """
    Indicates the status of an object
    """

    PRESENT = "present"
    """
    Defined in a Namespace, and known to exist on the Koji instance
    """

    PENDING = "pending"
    """
    Defined in a Namespace, but not known to exist on the Koji instance
    """

    DISCOVERED = "discovered"
    """
    Dependency which is not defined in a Namespace, but is known to exist on the Koji instance
    """

    PHANTOM = "phantom"
    """
    Dependency which is not defined in a Namespace, and not known to exist on the Koji instance
    """


class Identifiable(Protocol):

    def key(self) -> BaseKey:
        ...


# Pydantic Model Mixins

class IdentifiableMixin(Mixin):
    """
    Pydantic mixin for Identifiable protocol
    """

    typename: ClassVar[str] = 'object'

    name: str = Field(alias='name')
    yaml_type: Optional[str] = Field(alias='type', default=None)


    def model_post_init(self, __context: Any):
        if self.yaml_type is None:
            self.yaml_type = self.typename
        super().model_post_init(__context)


    @field_validator('name', mode='before')
    def validate_name(cls, value: str):
        value = value and value.strip()
        if not value:
            raise ValueError(f"name is required for {cls.typename}")
        return value


    def key(self) -> BaseKey:
        typekey = self.yaml_type or self.typename
        return (typekey, self.name)


    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.name})>"


LocalT = TypeVar('LocalT', bound='LocalMixin')


class LocalMixin(Mixin):
    """
    Pydantic mixin for Local protocol
    """

    filename: Optional[str] = Field(alias='__file__', default=None)
    lineno: Optional[int] = Field(alias='__line__', default=None)
    trace: Optional[List[Dict[str, Any]]] = Field(alias='__trace__', default_factory=list)

    _data: Optional[Dict[str, Any]] = PrivateAttr(default=None)


    def filepos(self) -> Tuple[Optional[str], Optional[int]]:
        return (self.filename, self.lineno)


    def filepos_str(self) -> str:
        filename = self.filename or '<unknown>'
        if self.lineno:
            return f"{filename}:{self.lineno}"
        else:
            return filename


    @classmethod
    def from_dict(cls: Type[LocalT], data: Dict[str, Any]) -> LocalT:
        """
        Create an instance directly from a dictionary. Records the original data
        dict for later review via the `data` property.
        """

        obj = cls.model_validate(data)
        obj._data = data
        return obj


    def to_dict(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Return a dictionary representation of this object. This is distinct from
        the original data that was used to create the object, and may include
        fields with default values and validated forms.
        """

        return self.model_dump(by_alias=True, **kwargs)


    @property
    def data(self) -> Optional[Dict[str, Any]]:
        """
        Access the raw data that was used if this object was created via `from_dict`
        """
        return self._data


class ResolvableMixin(Identifiable, Mixin):

    # We cannot make this a PrivateAttr because doing so breaks Pydantic v1.10
    # compatibility. This is because v1.10 creates a __slots__ attribute for the
    # class when there are private attributes, and you cannot use __slots__ with
    # multiple inheritance, which is the whole damned point of mixins. The _data
    # attribute from LocalMixin is the one that conflicts with us. Inheriting
    # from LocalMixin and ResolvableMixin together explodes pydantic v1.10
    _remote: Optional[VirtualCall] = None


    @property
    def status(self) -> BaseStatus:
        return BaseStatus.PRESENT if self.remote() is not None else BaseStatus.PENDING


    def is_phantom(self) -> bool:
        return False


    def remote(self):
        try:
            return self._remote.result if self._remote is not None else None
        except MultiCallNotReady:
            return None


    def load_remote(self, session: MultiCallSession, reload: bool = False) -> VirtualCall:
        if reload or self._remote is None:
            self._remote = self.query_remote(session, self.key())
        return self._remote


    @classmethod
    def query_remote(cls, session: MultiCallSession, key: BaseKey) -> VirtualCall:
        raise NotImplementedError("Subclasses must implement query_remote")


class SubModel(BaseModel):
    """
    A base model for submodels that need to be validated by alias and name.
    """
    pass


class CoreModel(IdentifiableMixin, BaseModel):
    """
    A base model shared by a core and remote object
    """

    def dependency_keys(self) -> Sequence[BaseKey]:
        return ()


CoreT = TypeVar('CoreT', bound='CoreObject')


class CoreObject(IdentifiableMixin, LocalMixin, ResolvableMixin, BaseModel):
    """
    Core models that load from YAML and have full functionality through
    the Resolver, Processor, and Solver.
    """

    typename: ClassVar[str] = 'object'

    _auto_split: ClassVar[bool] = False
    _is_split: bool = PrivateAttr(default=False)
    _was_split: bool = PrivateAttr(default=False)

    # pydantic v1.10 compatibility for ResolvableMixin
    _remote: Optional[VirtualCall] = PrivateAttr(default=None)


    def dependency_keys(self) -> Sequence[BaseKey]:
        return ()


    def key(self) -> BaseKey:
        """
        Return the key of this object as a tuple of (typename, name)
        """
        typekey = self.yaml_type or self.typename
        if self._is_split:
            typekey = f"{typekey}-split"
        return (typekey, self.name)


    def can_split(self) -> bool:
        return self._auto_split


    def was_split(self) -> bool:
        return self._was_split


    def is_split(self) -> bool:
        return self._is_split


    def split(self: CoreT) -> CoreT:
        if self._auto_split:
            child: CoreT = type(self)(name=self.name)
            child._is_split = True
            self._was_split = True
            return child
        else:
            raise TypeError(f"Cannot split {self.typename}")


    def change_report(self, resolver: 'Resolver') -> 'ChangeReport':
        raise NotImplementedError("Subclasses must implement change_report")


    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.name})>"


# temporary alias
BaseObject = CoreObject


RemoteT = TypeVar('RemoteT', bound='RemoteObject')


class RemoteObject(IdentifiableMixin, BaseModel):
    """
    Base models that load from the Koji API, and are used for comparison by a
    CoreObject
    """

    koji_id: int = Field(alias='id')


    def dependency_keys(self) -> Sequence[BaseKey]:
        return ()


    @classmethod
    def from_koji(cls: Type[RemoteT], data: Optional[Dict[str, Any]]) -> RemoteT:
        raise NotImplementedError("Subclasses must implement from_koji")


    def load_additional_data(self, session: MultiCallSession):
        pass  # Default implementation


    def to_dict(self, **kwargs: Any) -> Dict[str, Any]:
        return self.model_dump(by_alias=True, exclude={'koji_id'}, **kwargs)


    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.name})>"


# The end.

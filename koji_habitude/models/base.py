"""
koji_habitude.models.base

Base class for koji object models

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated with Human Rework


from enum import Enum
from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Optional,
    Protocol,
    Sequence,
    TYPE_CHECKING,
    Tuple,
    Type,
)

from typing_extensions import TypeAlias

from ..pydantic import BaseModel, ConfigDict, Field, field_validator, PYDANTIC_V2

from koji import MultiCallNotReady, MultiCallSession, VirtualCall

if TYPE_CHECKING:
    from .change import ChangeReport
    from ..resolver import Resolver


__all__ = (
    'Base',
    'BaseKey',
    'BaseStatus',
    'BaseObject',
    'SubModel',
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


class Base(Protocol):
    """
    Base protocol for all object models intended to be used in a Namespace, or
    fed to a Solver or Processor
    """

    typename: ClassVar[str]

    name: str

    filename: Optional[str]
    lineno: Optional[int]
    trace: Optional[List[Dict[str, Any]]]

    def key(self) -> BaseKey:
        ...

    def filepos(self) -> Tuple[Optional[str], Optional[int]]:
        ...

    def filepos_str(self) -> str:
        ...

    def is_phantom(self) -> bool:
        ...

    def can_split(self) -> bool:
        ...

    def was_split(self) -> bool:
        ...

    def is_split(self) -> bool:
        ...

    def split(self) -> Optional['Base']:
        ...

    def dependency_keys(self) -> Sequence[BaseKey]:
        ...

    @property
    def status(self) -> BaseStatus:
        """
        Indicates the status of this object
        """
        ...

    def exists(self) -> Any:
        """
        Indicates whether this object is known to exist on the Koji instance
        """
        ...

    def query_exists(self, session: MultiCallSession) -> VirtualCall:
        """
        Resolve the existence of this object on the Koji instance
        """
        ...

    @classmethod
    def check_exists(cls, session: MultiCallSession, key: BaseKey) -> Any:
        """
        Check the existence of a key of the given type and name on the Koji instance
        """
        ...

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Base':
        ...

    def to_dict(self) -> Dict[str, Any]:
        ...

    def change_report(self, resolver: 'Resolver') -> 'ChangeReport':
        ...


class SubModel(BaseModel):
    """
    A base model for submodels that need to be validated by alias and name.
    """

    if PYDANTIC_V2:
        model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)
    else:
        Config = ConfigDict(validate_by_alias=True, validate_by_name=True)  # type: ignore


# we need this to enable our inheritance of both the BaseModel from pydantic and
# the Protocol from typing
MetaModelProtocol: Type[type] = type("MetaModelProtocol", (type(BaseModel), type(Protocol)), {})


class BaseObject(BaseModel):  # , metaclass=MetaModelProtocol): # type: ignore
    """
    Adapter between the Base protocol and Pydantic models.
    """

    typename: ClassVar[str] = 'object'

    name: str = Field(alias='name')
    yaml_type: Optional[str] = Field(alias='type', default=None)
    filename: Optional[str] = Field(alias='__file__', default=None)
    lineno: Optional[int] = Field(alias='__line__', default=None)
    trace: Optional[List[Dict[str, Any]]] = Field(alias='__trace__', default_factory=list)

    # this is the record of the `from_dict` call if it was used
    _data: Optional[Dict[str, Any]] = None
    _exists: Optional[VirtualCall] = None

    _auto_split: ClassVar[bool] = False
    _is_split: bool = False    # True if this is the minimal copy of a split
    _was_split: bool = False   # True if this object has been split


    if PYDANTIC_V2:
        model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

    else:
        Config = ConfigDict(validate_by_alias=True, validate_by_name=True)  # type: ignore

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.model_post_init(None)

        def model_post_init(self, __context: Any):
            pass


    @field_validator('name', mode='before')
    @classmethod
    def validate_name(cls, value: str):
        value = value and value.strip()
        if not value:
            raise ValueError(f"name is required for {cls.typename}")
        return value


    @property
    def status(self) -> BaseStatus:
        # Reference objects will override this to return DISCOVERED or PHANTOM. But since
        # objects of our types will always exist due to being defied in the Namespace,
        # we don't worry about the Reference cases here.
        return BaseStatus.PRESENT if self.exists() is not None else BaseStatus.PENDING


    def is_phantom(self) -> bool:
        return False


    def exists(self) -> Any:
        # Check the value of the VirtualCall returned by the last `query_exists`
        # call.
        try:
            return self._exists.result if self._exists is not None else None
        except MultiCallNotReady:
            return None


    def query_exists(self, session: MultiCallSession) -> VirtualCall:
        # the default implementation defers to `check_exists` so that subclasses
        # only need to implement that classmethod to provide the existence
        # check.
        res = self.check_exists(session, self.key())
        if isinstance(res, VirtualCall):
            self._exists = res
        else:
            self._exists = VirtualCall(None, None, None)
            self._exists._result = res
        return self._exists


    @classmethod
    def check_exists(cls, session: MultiCallSession, key: BaseKey) -> VirtualCall:
        raise NotImplementedError("Subclasses of BaseObject must implement check_exists")


    if PYDANTIC_V2:
        # Pydantic v2 is preferred
        @classmethod
        def from_dict(cls, data: Dict[str, Any]) -> 'BaseObject':
            """
            Create an instance directly from a dictionary. Records the original data
            dict for later review via the `data` property.
            """
            obj = cls.model_validate(data)
            obj._data = data
            return obj


        def to_dict(self) -> Dict[str, Any]:
            """
            Return a dictionary representation of this object. This is distinct from
            the original data that was used to create the object, and may include
            fields with default values and validated forms.
            """
            return self.model_dump(by_alias=True)

    else:
        # Pydantic v1 compatibility
        @classmethod
        def from_dict(cls, data: Dict[str, Any]) -> 'BaseObject':
            """
            Create an instance directly from a dictionary. Records the original data
            dict for later review via the `data` property.
            """
            obj = cls.parse_obj(data)
            obj._data = data
            return obj

        def to_dict(self) -> Dict[str, Any]:
            """
            Return a dictionary representation of this object. This is distinct from
            the original data that was used to create the object, and may include
            fields with default values and validated forms.
            """
            return self.dict(by_alias=True)


    @property
    def data(self) -> Optional[Dict[str, Any]]:
        """
        Access the raw data that was used if this object was created via `from_dict`
        """
        return self._data


    def key(self) -> BaseKey:
        """
        Return the key of this object as a tuple of (typename, name)
        """

        typekey = self.yaml_type or self.typename
        if self._is_split:
            typekey = f"{typekey}-split"
        return (typekey, self.name)


    def filepos(self) -> Tuple[Optional[str], Optional[int]]:
        """
        Return the file position of this object as a tuple of (filename, lineno)
        """
        return (self.filename, self.lineno)


    def filepos_str(self) -> str:
        """
        Return a string representation of the file position of this object
        """
        filename = self.filename or '<unknown>'
        if self.lineno:
            return f"{filename}:{self.lineno}"
        else:
            return filename


    def can_split(self) -> bool:
        """
        True if this object can be split in order to break cyclic dependencies
        """
        return self._auto_split


    def was_split(self) -> bool:
        """
        True if this object was split by a change report
        """
        return self._was_split


    def is_split(self) -> bool:
        """
        True if this object is a split of another object
        """
        return self._is_split


    def split(self) -> 'BaseObject':
        """
        If the object supports splitting, create a minimal copy of this object
        specifying only that it needs to exist, with a dependant link on the
        original object. Otherwise raise a TypeError.
        """
        if self._auto_split:
            child = type(self)(name=self.name)
            child._is_split = True
            self._was_split = True
            return child
        else:
            raise TypeError(f"Cannot split {self.typename}")


    def dependency_keys(self) -> Sequence[BaseKey]:
        """
        Return the keys of the dependencies of this object as a sequence of
        (typename, name) tuples
        """
        return ()


    def change_report(self, resolver: 'Resolver') -> 'ChangeReport':
        raise NotImplementedError("Subclasses of BaseObject must implement change_report")


    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.name})>"


# The end.

"""
koji-habitude - pydantic

Pydantic compatibility layer for supporting both v1.10 and v2.x

This module provides a unified interface that works with both pydantic 1.10
(shipped with RHEL 9) and pydantic 2.x.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 4.5 Sonnet via Cursor
"""


from typing import Any, Callable, Dict, Optional, Type, TypeVar
from pydantic import BaseModel as _BaseModel, Field


__all__ = (
    'BaseModel',
    'Field',
    'field_validator',
)


try:
    # Pydantic v2 imports
    from pydantic import ConfigDict
    from pydantic import field_validator

    class BaseModel(_BaseModel):
        model_config = ConfigDict(validate_by_alias=True, validate_by_name=True)

except ImportError:
    # Pydantic v1.10 compatibility
    from pydantic import validator as _validator

    T = TypeVar('T', bound='BaseModel')

    class BaseModel(_BaseModel):  # type: ignore
        # This is a compatability shim for pydantic v1.10 to look more like v2

        class Config:
            allow_population_by_field_name = True
            underscore_attrs_are_private = True

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.model_post_init(None)

        def model_post_init(self, __context: Any):
            pass

        @classmethod
        def model_validate(cls: Type[T], data: Dict[str, Any]) -> T:  # type: ignore
            """
            Create an instance directly from a dictionary. Records the original data
            dict for later review via the `data` property.
            """
            return cls.parse_obj(data)

        def model_dump(self, by_alias: bool = True) -> Dict[str, Any]:  # type: ignore
            """
            Return a dictionary representation of this object. This is distinct from
            the original data that was used to create the object, and may include
            fields with default values and validated forms.
            """
            return self.dict(by_alias=by_alias)

    def field_validator(  # type: ignore
            field: str,
            *fields: str,
            mode: str = 'after',
            check_fields: Optional[bool] = None) -> Callable:
        """
        Compatibility wrapper for pydantic v1 validator.

        Translates v2's field_validator to v1's validator decorator.
        """

        pre = (mode == 'before')

        def decorator(func: Callable) -> Callable:
            if pre:
                work = func
            else:
                work = lambda cls, v, values=None: func(cls, v)
            return _validator(field, *fields, pre=pre, always=True, allow_reuse=True)(work)

        return decorator


# The end.

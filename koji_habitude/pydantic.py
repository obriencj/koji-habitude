"""
koji-habitude - pydantic

Pydantic compatibility layer for supporting both v1.10 and v2.x

This module provides a unified interface that works with both pydantic 1.10
(shipped with RHEL 9) and pydantic 2.x.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 4.5 Sonnet via Cursor
"""


import pydantic
from typing import Any, Callable, Dict, Optional, Type, TypeVar


__all__ = (
    'PYDANTIC_V2',
    'BaseModel',
    'Field',
    'ValidationError',
    'field_validator',
    'model_validator',
    'ConfigDict',
)


# Detect pydantic version
PYDANTIC_V2 = pydantic.VERSION.startswith('2.')


# Re-export common items that work the same in both versions
from pydantic import BaseModel, Field, ValidationError


if PYDANTIC_V2:
    # Pydantic v2 imports
    from pydantic import field_validator
    from pydantic import model_validator
    from pydantic import ConfigDict

else:
    # Pydantic v1.10 compatibility shims
    from pydantic import validator as _validator
    from pydantic import root_validator as _root_validator
    from functools import wraps

    def field_validator(  # type: ignore
        field: str,
        *fields: str,
        mode: str = 'after',
        check_fields: Optional[bool] = None,
    ) -> Callable:
        """
        Compatibility wrapper for pydantic v1 validator.

        Translates v2's field_validator to v1's validator decorator.
        """

        # In v2: mode='before' or mode='after'
        # In v1: pre=True or pre=False
        pre = (mode == 'before')

        all_fields = (field,) + fields

        def decorator(func: Callable) -> Callable:
            # v1 validator expects (cls, value, values, field, config) for validators
            # v2 field_validator expects (cls, value) for mode='after'
            # We need to adapt the signature

            # unwrap the function if it's a classmethod
            if isinstance(func, classmethod):
                func = func.__func__

            if pre:
                # For pre=True validators, v1 passes: cls, v
                # which matches v2's mode='before' signature
                return _validator(*all_fields, pre=True, always=True, allow_reuse=True)(func)
            else:
                # For pre=False validators, v1 passes: cls, v, values
                # but v2 mode='after' only expects: cls, v
                # We need to wrap to ignore the extra 'values' parameter
                @wraps(func)
                def wrapper(cls, v, values=None):
                    return func(cls, v)

                return _validator(*all_fields, pre=False, always=True, allow_reuse=True)(wrapper)

        return decorator


    def model_validator(*, mode: str) -> Callable:  # type: ignore
        """
        Compatibility wrapper for pydantic v1 root_validator.

        Translates v2's model_validator to v1's root_validator decorator.
        """

        # In v2: mode='before' or mode='after'
        # In v1: pre=True or pre=False
        pre = (mode == 'before')

        def decorator(func: Callable) -> Callable:
            # root_validator signature is the same in v1
            return _root_validator(pre=pre, allow_reuse=True)(func)  # type: ignore

        return decorator


    def ConfigDict(  # type: ignore
            validate_by_alias: bool = False,
            validate_by_name: bool = False):
        config = {
            'validate_assignment_by_alias': validate_by_alias,
            'validate_assignment_by_name': validate_by_name,
            'underscore_attrs_are_private': True,
        }
        return type('Config', (), config)


# The end.

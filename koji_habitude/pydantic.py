"""
koji-habitude - pydantic

Pydantic compatibility layer for supporting both v1.10 and v2.x

This module provides a unified interface that works with both pydantic 1.10
(shipped with RHEL 9) and pydantic 2.x.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 4.5 Sonnet via Cursor
"""


from typing import Callable,  Optional
from pydantic import VERSION, BaseModel, Field, ValidationError


__all__ = (
    'PYDANTIC_V2',
    'BaseModel',
    'Field',
    'ValidationError',
    'field_validator',
    'ConfigDict',
)


# Detect pydantic version
PYDANTIC_V2 = VERSION.startswith('2.')


try:
    # Pydantic v2 imports
    from pydantic import ConfigDict
    from pydantic import field_validator

except ImportError:
    ConfigDict = None  # type: ignore

    # Pydantic v1.10 compatibility shims
    from pydantic import validator as _validator
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

        pre = (mode == 'before')

        def decorator(func: Callable) -> Callable:
            if pre:
                work = func
            else:
                work = lambda cls, v, values=None: func(cls, v)
            return _validator(field, *fields, pre=pre, always=True, allow_reuse=True)(work)

        return decorator


# The end.

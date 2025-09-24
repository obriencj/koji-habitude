"""
koji-habitude - models.permission

Permission model for koji permission objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""


from typing import ClassVar, Optional

from pydantic import Field

from .base import BaseKojiObject


class Permission(BaseKojiObject):
    """
    Koji permission object model.
    """

    typename: ClassVar[str] = "permission"

    description: Optional[str] = Field(alias='description', default=None)


# The end.

"""
koji-habitude - models.external_repo

External repository model for koji external repo objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""


from typing import ClassVar

from pydantic import Field

from .base import BaseKojiObject


class ExternalRepo(BaseKojiObject):
    """
    Koji external repository object model.
    """

    typename: ClassVar[str] = "external-repo"

    url: str = Field(alias='url', pattern=r'^https?://')


# The end.

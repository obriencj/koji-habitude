"""
koji-habitude - models.user

User model for koji user objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

from typing import Dict, List, Tuple, Any
from .base import BaseKojiObject


class User(BaseKojiObject):
    """
    Koji user object model.
    """

    typename = "user"


    def dependent_keys(self) -> List[Tuple[str, str]]:
        """
        Return dependencies for this user.

        Users typically have no dependencies on other koji objects.
        They are usually leaf nodes in the dependency tree.
        """

        return []

# The end.

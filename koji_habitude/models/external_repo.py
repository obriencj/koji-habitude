"""
koji-habitude - models.external_repo

External repository model for koji external repo objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

from typing import Dict, List, Tuple, Any
from .base import BaseKojiObject


class ExternalRepo(BaseKojiObject):
    """
    Koji external repository object model.
    """

    def dependent_keys(self) -> List[Tuple[str, str]]:
        """
        Return dependencies for this external repo.

        External repos depend on:
        - Tags they are associated with
        """

        deps = []

        # Check for tag dependency
        tag = self.data.get('tag')
        if tag:
            deps.append(('tag', tag))

        return deps

# The end.
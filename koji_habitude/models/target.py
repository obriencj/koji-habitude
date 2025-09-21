"""
koji-habitude - models.target

Target model for koji build target objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

from typing import Dict, List, Tuple, Any
from .base import BaseKojiObject


class Target(BaseKojiObject):
    """
    Koji build target object model.
    """

    typename = "target"


    def dependent_keys(self) -> List[Tuple[str, str]]:
        """
        Return dependencies for this target.

        Targets depend on:
        - Build tag
        - Destination tag
        """

        deps = []

        # Build tag dependency
        build_tag = self.data.get('build_tag')
        if build_tag:
            deps.append(('tag', build_tag))

        # Destination tag dependency
        dest_tag = self.data.get('dest_tag')
        if dest_tag:
            deps.append(('tag', dest_tag))

        return deps

# The end.

"""
koji-habitude - models.host

Host model for koji build host objects.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

from typing import Dict, List, Tuple, Any
from .base import BaseKojiObject


class Host(BaseKojiObject):
    """
    Koji build host object model.
    """
    
    def dependent_keys(self) -> List[Tuple[str, str]]:
        """
        Return dependencies for this host.
        
        Hosts may depend on:
        - Users (for ownership/permissions)
        """
        
        deps = []
        
        # User dependency for host ownership
        user = self.data.get('user')
        if user:
            deps.append(('user', user))
            
        return deps

# The end.
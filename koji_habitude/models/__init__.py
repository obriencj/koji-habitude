"""
koji-habitude - models

Core koji object models package.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

from .base import BaseKojiObject
from .tag import Tag
from .external_repo import ExternalRepo
from .user import User
from .target import Target
from .host import Host
from .group import Group

# Registry of core model types
CORE_MODELS = {
    'tag': Tag,
    'external-repo': ExternalRepo,
    'user': User,
    'target': Target,
    'host': Host,
    'group': Group,
}

__all__ = [
    'BaseKojiObject',
    'Tag',
    'ExternalRepo', 
    'User',
    'Target',
    'Host',
    'Group',
    'CORE_MODELS',
]

# The end.
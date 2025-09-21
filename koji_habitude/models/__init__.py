"""
koji-habitude - models

Core koji object models package.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated with Human Rework


from .base import Base, BaseObject, BaseKojiObject, RawObject
from .tag import Tag
from .external_repo import ExternalRepo
from .user import User
from .target import Target
from .host import Host
from .group import Group


__all__ = (
    'CORE_MODELS',

    'Base',
    'BaseObject',
    'RawObject',

    'BaseKojiObject',
    'ExternalRepo',
    'Group',
    'Host',
    'Tag',
    'Target',
    'User',
)


CORE_MODELS = (
    ExternalRepo,
    Group,
    Host,
    Tag,
    Target,
    User,
)


# The end.

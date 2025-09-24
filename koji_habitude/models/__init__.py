"""
koji-habitude - models

Core koji object models package.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated with Human Rework


from .base import Base, BaseKojiObject, BaseObject, RawObject
from .channel import Channel
from .external_repo import ExternalRepo
from .group import Group
from .host import Host
from .permission import Permission
from .tag import Tag
from .target import Target
from .user import User


__all__ = (
    'CORE_MODELS',

    'Base',
    'BaseObject',
    'RawObject',
    'BaseKojiObject',

    'Channel',
    'ExternalRepo',
    'Group',
    'Host',
    'Permission',
    'Tag',
    'Target',
    'User',
)


CORE_MODELS = (
    Channel,
    ExternalRepo,
    Group,
    Host,
    Permission,
    Tag,
    Target,
    User,
)


# The end.

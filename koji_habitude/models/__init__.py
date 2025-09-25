"""
koji-habitude - models

Core koji object models package.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated with Human Rework


from typing import Tuple, Type
from types import MappingProxyType


from .base import Base, BaseKojiObject, BaseObject, BaseKey
from .change import ChangeReport
from .channel import Channel
from .external_repo import ExternalRepo
from .group import Group
from .host import Host
from .permission import Permission
from .tag import Tag
from .target import Target
from .user import User


__all__ = (
    'CORE_TYPES',
    'CORE_MODELS',

    'Base',
    'BaseObject',
    'BaseKey',
    'BaseKojiObject',
    'ChangeReport',

    'Channel',
    'ExternalRepo',
    'Group',
    'Host',
    'Permission',
    'Tag',
    'Target',
    'User',
)


CORE_TYPES: Tuple[Type[BaseKojiObject], ...] = (
    Channel,
    ExternalRepo,
    Group,
    Host,
    Permission,
    Tag,
    Target,
    User,
)

CORE_MODELS: MappingProxyType[str, Type[BaseKojiObject]] = MappingProxyType({tp.typename: tp for tp in CORE_TYPES})


# The end.

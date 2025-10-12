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


from .base import Base, BaseObject, BaseKey, BaseStatus
from .change import ChangeReport, Change, Create, Update, Add, Remove, Modify
from .channel import Channel
from .content_generator import ContentGenerator
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
    'BaseStatus',

    'Change',
    'ChangeReport',
    'Create',
    'Update',
    'Add',
    'Remove',
    'Modify',

    'Channel',
    'ContentGenerator',
    'ExternalRepo',
    'Group',
    'Host',
    'Permission',
    'Tag',
    'Target',
    'User',
)


CORE_TYPES: Tuple[Type[BaseObject], ...] = (
    Channel,
    ContentGenerator,
    ExternalRepo,
    Group,
    Host,
    Permission,
    Tag,
    Target,
    User,
)

CORE_MODELS: MappingProxyType[str, Type[BaseObject]] = \
     MappingProxyType({tp.typename: tp for tp in CORE_TYPES})


# The end.

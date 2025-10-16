"""
koji-habitude - models

Core koji object models package.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated with Human Rework


from types import MappingProxyType
from typing import Mapping, Tuple, Type

from .archive_type import ArchiveType
from .base import Base, BaseKey, BaseObject, BaseStatus
from .build_type import BuildType
from .change import Add, Change, ChangeReport, Create, Modify, Remove, Update
from .channel import Channel
from .compat import Field, field_validator
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

    'Field',
    'field_validator',

    'Change',
    'ChangeReport',
    'Create',
    'Update',
    'Add',
    'Remove',
    'Modify',

    'ArchiveType',
    'BuildType',
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
    ArchiveType,
    BuildType,
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

CORE_MODELS: Mapping[str, Type[BaseObject]] = \
     MappingProxyType({tp.typename: tp for tp in CORE_TYPES})


# The end.

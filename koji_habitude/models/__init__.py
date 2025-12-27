"""
koji-habitude - models

Core koji object models package.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated with Human Rework


from typing import Dict, List, Type

from .archive_type import ArchiveType
from .base import (
    BaseKey, BaseObject, BaseStatus, CoreModel, CoreObject, DataMixin,
    IdentifiableMixin, LocalMixin, ResolvableMixin, SubModel,
)
from .build_type import BuildType
from .change import Add, Change, ChangeReport, Create, Modify, Remove, Update
from .channel import Channel
from .compat import BaseModel, Field, PrivateAttr, field_validator
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

    # Base protocols and classes
    'BaseObject',
    'BaseKey',
    'BaseStatus',
    'CoreModel',
    'CoreObject',

    # Pydantic mixins
    'DataMixin',
    'IdentifiableMixin',
    'LocalMixin',
    'ResolvableMixin',

    # Compat
    'BaseModel',
    'SubModel',
    'Field',
    'PrivateAttr',
    'field_validator',

    # Change classes
    'Change',
    'ChangeReport',
    'Create',
    'Update',
    'Add',
    'Remove',
    'Modify',

    # Core models
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


CORE_TYPES: List[Type[CoreObject]] = [
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
]


CORE_MODELS: Dict[str, Type[CoreObject]] = {
    tp.typename: tp for tp in CORE_TYPES
}


# The end.

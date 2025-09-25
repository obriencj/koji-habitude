"""
koji-habitude - models.change

Base classes for Change and ChangeReport

Each model needs to subclass these in order to fully represent their changes
when comparing to the data in a koji instance.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: Pure Human


from enum import Enum
from typing import Any, Optional

from .base import BaseKey


class ChangeMode(Enum):
    CREATE = 'create'
    UPDATE = 'update'
    DELETE = 'delete'


class Change:
    def __init__(self, mode: ChangeMode, old: Optional[Any], new: Optional[Any]):
        self.mode: ChangeMode = mode
        self.old: Optional[Any] = old
        self.new: Optional[Any] = new


class ChangeReport:

    def __init__(self, key: BaseKey):
        self.key = key
        self.changes = []


    def add_change(self, change: Change):
        self.changes.append(change)


# The end.

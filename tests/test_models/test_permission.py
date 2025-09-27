"""
koji-habitude - test_permission

Unit tests for koji_habitude.models.Permission.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

import unittest

from koji_habitude.models import Permission


class TestPermissionModel(unittest.TestCase):
    """
    Test the Permission model.
    """

    def test_permission_creation(self):
        """
        Test Permission creation (name-only object).
        """

        data = {'type': 'permission', 'name': 'admin'}
        permission = Permission.from_dict(data)

        self.assertEqual(permission.typename, 'permission')
        self.assertEqual(permission.name, 'admin')
        self.assertFalse(permission.can_split())

    def test_permission_dependency_keys(self):
        """
        Test Permission has no dependencies.
        """

        data = {'type': 'permission', 'name': 'admin'}
        permission = Permission.from_dict(data)

        deps = permission.dependency_keys()
        self.assertEqual(deps, ())


# The end.

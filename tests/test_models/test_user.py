"""
koji-habitude - test_user

Unit tests for koji_habitude.models.User.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

import unittest

from koji_habitude.models import User


class TestUserModel(unittest.TestCase):
    """
    Test the User model.
    """

    def test_user_creation_with_defaults(self):
        """
        Test User creation with default values.
        """

        data = {'type': 'user', 'name': 'test-user'}
        user = User.from_dict(data)

        self.assertEqual(user.typename, 'user')
        self.assertEqual(user.name, 'test-user')
        self.assertEqual(user.groups, [])
        self.assertEqual(user.permissions, [])
        self.assertIsNone(user.enabled)
        self.assertTrue(user.can_split())

    def test_user_creation_with_all_fields(self):
        """
        Test User creation with all fields specified.
        """

        data = {
            'type': 'user',
            'name': 'test-user',
            'groups': ['group1', 'group2'],
            'permissions': ['admin', 'build'],
            'enabled': False
        }
        user = User.from_dict(data)

        self.assertEqual(user.groups, ['group1', 'group2'])
        self.assertEqual(user.permissions, ['admin', 'build'])
        self.assertFalse(user.enabled)

    def test_user_split(self):
        """
        Test User splitting functionality.
        """

        data = {
            'type': 'user',
            'name': 'test-user',
            'groups': ['group1', 'group2'],
            'permissions': ['admin', 'build'],
            'enabled': False
        }
        user = User.from_dict(data)
        split_user = user.split()
        self.assertIsInstance(split_user, User)
        self.assertEqual(split_user.name, 'test-user')
        self.assertEqual(split_user.groups, [])
        self.assertEqual(split_user.permissions, [])
        self.assertFalse(split_user.enabled)

    def test_user_dependency_keys(self):
        """
        Test User dependency resolution.
        """

        data = {
            'type': 'user',
            'name': 'test-user',
            'groups': ['group1', 'group2'],
            'permissions': ['admin', 'build']
        }
        user = User.from_dict(data)

        deps = user.dependency_keys()
        expected = [
            ('group', 'group1'),
            ('group', 'group2'),
            ('permission', 'admin'),
            ('permission', 'build')
        ]
        self.assertEqual(deps, expected)

    def test_user_dependency_keys_empty(self):
        """
        Test User dependency resolution with no groups or permissions.
        """

        data = {'type': 'user', 'name': 'test-user'}
        user = User.from_dict(data)

        deps = user.dependency_keys()
        self.assertEqual(deps, [])


# The end.

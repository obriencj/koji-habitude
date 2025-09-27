"""
koji-habitude - test_group

Unit tests for koji_habitude.models.Group.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

import unittest

from koji_habitude.models import Group


class TestGroupModel(unittest.TestCase):
    """
    Test the Group model.
    """

    def test_group_creation_with_defaults(self):
        """
        Test Group creation with default values.
        """

        data = {'type': 'group', 'name': 'test-group'}
        group = Group.from_dict(data)

        self.assertEqual(group.typename, 'group')
        self.assertEqual(group.name, 'test-group')
        self.assertEqual(group.members, [])
        self.assertEqual(group.permissions, [])
        self.assertTrue(group.can_split())

    def test_group_creation_with_members_and_permissions(self):
        """
        Test Group creation with members and permissions.
        """

        data = {
            'type': 'group',
            'name': 'test-group',
            'members': ['user1', 'user2'],
            'permissions': ['admin', 'build']
        }
        group = Group.from_dict(data)

        self.assertEqual(group.members, ['user1', 'user2'])
        self.assertEqual(group.permissions, ['admin', 'build'])

    def test_group_dependency_keys(self):
        """
        Test Group dependency resolution.
        """

        data = {
            'type': 'group',
            'name': 'test-group',
            'members': ['user1', 'user2'],
            'permissions': ['admin', 'build']
        }
        group = Group.from_dict(data)

        deps = group.dependency_keys()
        expected = [
            ('user', 'user1'),
            ('user', 'user2'),
            ('permission', 'admin'),
            ('permission', 'build')
        ]
        self.assertEqual(deps, expected)

    def test_group_dependency_keys_empty(self):
        """
        Test Group dependency resolution with no members or permissions.
        """

        data = {'type': 'group', 'name': 'test-group'}
        group = Group.from_dict(data)

        deps = group.dependency_keys()
        self.assertEqual(deps, [])


# The end.

"""
koji-habitude - test_content_generator

Unit tests for koji_habitude.models.ContentGenerator.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 4.5 Sonnet via Cursor
"""

import unittest

from koji_habitude.models import ContentGenerator


class TestContentGeneratorModel(unittest.TestCase):
    """
    Test the ContentGenerator model.
    """

    def test_content_generator_creation_with_defaults(self):
        """
        Test ContentGenerator creation with default values.
        """

        data = {'type': 'content-generator', 'name': 'test-cg'}
        cg = ContentGenerator.from_dict(data)

        self.assertEqual(cg.typename, 'content-generator')
        self.assertEqual(cg.name, 'test-cg')
        self.assertEqual(cg.users, [])
        self.assertFalse(cg.exact_users)
        self.assertFalse(cg.can_split())

    def test_content_generator_creation_with_all_fields(self):
        """
        Test ContentGenerator creation with all fields specified.
        """

        data = {
            'type': 'content-generator',
            'name': 'test-cg',
            'users': ['user1', 'user2', 'user3'],
            'exact-users': True
        }
        cg = ContentGenerator.from_dict(data)

        self.assertEqual(cg.name, 'test-cg')
        self.assertEqual(cg.users, ['user1', 'user2', 'user3'])
        self.assertTrue(cg.exact_users)

    def test_content_generator_dependency_keys(self):
        """
        Test ContentGenerator dependency resolution with users.
        """

        data = {
            'type': 'content-generator',
            'name': 'test-cg',
            'users': ['user1', 'user2']
        }
        cg = ContentGenerator.from_dict(data)

        deps = cg.dependency_keys()
        expected = [('user', 'user1'), ('user', 'user2')]
        self.assertEqual(deps, expected)

    def test_content_generator_dependency_keys_empty(self):
        """
        Test ContentGenerator dependency resolution with no users.
        """

        data = {'type': 'content-generator', 'name': 'test-cg'}
        cg = ContentGenerator.from_dict(data)

        deps = cg.dependency_keys()
        self.assertEqual(deps, [])

    def test_content_generator_exact_users_field(self):
        """
        Test ContentGenerator exact-users field defaults and assignment.
        """

        # Test default is False
        data = {'type': 'content-generator', 'name': 'test-cg'}
        cg = ContentGenerator.from_dict(data)
        self.assertFalse(cg.exact_users)

        # Test explicit True
        data = {
            'type': 'content-generator',
            'name': 'test-cg',
            'exact-users': True
        }
        cg = ContentGenerator.from_dict(data)
        self.assertTrue(cg.exact_users)

        # Test explicit False
        data = {
            'type': 'content-generator',
            'name': 'test-cg',
            'exact-users': False
        }
        cg = ContentGenerator.from_dict(data)
        self.assertFalse(cg.exact_users)


# The end.

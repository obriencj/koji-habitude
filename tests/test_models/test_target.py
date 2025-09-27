"""
koji-habitude - test_target

Unit tests for koji_habitude.models.Target.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

import unittest

from koji_habitude.models import Target


class TestTargetModel(unittest.TestCase):
    """
    Test the Target model.
    """

    def test_target_creation_with_build_tag(self):
        """
        Test Target creation with build-tag specified.
        """

        data = {
            'type': 'target',
            'name': 'test-target',
            'build-tag': 'build-tag'
        }
        target = Target.from_dict(data)

        self.assertEqual(target.typename, 'target')
        self.assertEqual(target.name, 'test-target')
        self.assertEqual(target.build_tag, 'build-tag')
        self.assertEqual(target.dest_tag, None)
        self.assertFalse(target.can_split())

    def test_target_creation_with_both_tags(self):
        """
        Test Target creation with both build-tag and dest-tag specified.
        """

        data = {
            'type': 'target',
            'name': 'test-target',
            'build-tag': 'build-tag',
            'dest-tag': 'dest-tag'
        }
        target = Target.from_dict(data)

        self.assertEqual(target.build_tag, 'build-tag')
        self.assertEqual(target.dest_tag, 'dest-tag')

    def test_target_model_post_init_sets_dest_tag(self):
        """
        Test that model_post_init sets dest_tag to name when not specified.
        """

        data = {
            'type': 'target',
            'name': 'test-target',
            'build-tag': 'build-tag'
            # dest-tag not specified
        }
        target = Target.from_dict(data)

        self.assertEqual(target.dest_tag, None)

    def test_target_dependency_keys(self):
        """
        Test Target dependency resolution.
        """

        data = {
            'type': 'target',
            'name': 'test-target',
            'build-tag': 'build-tag',
            'dest-tag': 'dest-tag'
        }
        target = Target.from_dict(data)

        deps = target.dependency_keys()
        expected = [('tag', 'build-tag'), ('tag', 'dest-tag')]
        self.assertEqual(deps, expected)


# The end.

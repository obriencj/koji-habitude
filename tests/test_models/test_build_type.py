"""
koji-habitude - test_build_type

Unit tests for koji_habitude.models.BuildType.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 4.5 Sonnet via Cursor
"""

import unittest

from koji_habitude.models import BuildType


class TestBuildTypeModel(unittest.TestCase):
    """
    Test the BuildType model.
    """

    def test_build_type_creation(self):
        """
        Test BuildType creation (name-only object).
        """

        data = {'type': 'build-type', 'name': 'rpm'}
        build_type = BuildType.from_dict(data)

        self.assertEqual(build_type.typename, 'build-type')
        self.assertEqual(build_type.name, 'rpm')
        self.assertFalse(build_type.can_split())

    def test_build_type_dependency_keys(self):
        """
        Test BuildType has no dependencies.
        """

        data = {'type': 'build-type', 'name': 'maven'}
        build_type = BuildType.from_dict(data)

        deps = build_type.dependency_keys()
        self.assertEqual(deps, ())


# The end.

"""
koji-habitude - test_registry

Unit tests for koji_habitude.models CORE_TYPES registry.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

import unittest

from koji_habitude.models import (
    CORE_MODELS, CORE_TYPES, BaseObject, Channel, ExternalRepo,
    Group, Host, Permission, Tag, Target, User,
)


class TestCoreModelsRegistry(unittest.TestCase):
    """
    Test the CORE_TYPES registry and model consistency.
    """

    def test_core_models_contains_all_expected_models(self):
        """
        Test that CORE_TYPES contains all expected model classes.
        """

        expected_models = [
            Channel,
            ExternalRepo,
            Group,
            Host,
            Permission,
            Tag,
            Target,
            User,
        ]

        self.assertEqual(len(CORE_TYPES), len(expected_models))

        for model_class in expected_models:
            self.assertIn(model_class, CORE_TYPES)

    def test_core_models_have_correct_typenames(self):
        """
        Test that all CORE_TYPES have correct typename attributes.
        """

        expected_typenames = {
            Channel: 'channel',
            ExternalRepo: 'external-repo',
            Group: 'group',
            Host: 'host',
            Permission: 'permission',
            Tag: 'tag',
            Target: 'target',
            User: 'user',
        }

        for model_class in CORE_TYPES:
            expected_typename = expected_typenames[model_class]
            self.assertEqual(model_class.typename, expected_typename)

    def test_core_models_instantiation_with_minimal_data(self):
        """
        Test that all CORE_TYPES can be instantiated with minimal data.
        """

        minimal_data_templates = {
            Channel: {'type': 'channel', 'name': 'test'},
            ExternalRepo: {'type': 'external-repo', 'name': 'test', 'url': 'https://example.com'},
            Group: {'type': 'group', 'name': 'test'},
            Host: {'type': 'host', 'name': 'test'},
            Permission: {'type': 'permission', 'name': 'test'},
            Tag: {'type': 'tag', 'name': 'test'},
            Target: {'type': 'target', 'name': 'test', 'build-tag': 'build-tag'},
            User: {'type': 'user', 'name': 'test'},
        }

        for model_class in CORE_TYPES:
            data = minimal_data_templates[model_class]
            obj = model_class.from_dict(data)
            self.assertIsInstance(obj, BaseObject)
            self.assertEqual(obj.name, 'test')

    def test_core_models_dependency_keys_return_tuples(self):
        """
        Test that all CORE_TYPES dependency_keys() methods return proper tuples.
        """

        minimal_data_templates = {
            Channel: {'type': 'channel', 'name': 'test'},
            ExternalRepo: {'type': 'external-repo', 'name': 'test', 'url': 'https://example.com'},
            Group: {'type': 'group', 'name': 'test'},
            Host: {'type': 'host', 'name': 'test'},
            Permission: {'type': 'permission', 'name': 'test'},
            Tag: {'type': 'tag', 'name': 'test'},
            Target: {'type': 'target', 'name': 'test', 'build-tag': 'build-tag'},
            User: {'type': 'user', 'name': 'test'},
        }

        for model_class in CORE_TYPES:
            data = minimal_data_templates[model_class]
            obj = model_class.from_dict(data)
            deps = obj.dependency_keys()

            self.assertIsInstance(deps, (list, tuple))
            for dep in deps:
                self.assertIsInstance(dep, tuple)
                self.assertEqual(len(dep), 2)
                self.assertIsInstance(dep[0], str)  # type
                self.assertIsInstance(dep[1], str)  # name


# The end.

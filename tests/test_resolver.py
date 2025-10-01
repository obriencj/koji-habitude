"""
koji-habitude - test_resolver

Unit tests for koji_habitude.resolver module.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated

import unittest
from pathlib import Path
from unittest.mock import Mock

from koji_habitude.resolver import Resolver, MissingObject, Report
from koji_habitude.namespace import Namespace
from koji_habitude.models import Tag, User, ExternalRepo, Target


class TestMissingObject(unittest.TestCase):
    """Test the MissingObject placeholder class."""

    def test_missing_object_creation(self):
        """Test creating a MissingObject with a key."""
        key = ('tag', 'missing-tag')
        missing = MissingObject(Tag, key)

        self.assertEqual(missing.typename, 'missing')
        self.assertEqual(missing.name, 'missing-tag')
        self.assertEqual(missing.yaml_type, 'tag')
        self.assertEqual(missing.key(), key)

    def test_missing_object_filepos(self):
        """Test that MissingObject returns None for file position."""
        key = ('user', 'missing-user')
        missing = MissingObject(User, key)

        filename, lineno = missing.filepos()
        self.assertIsNone(filename)
        self.assertIsNone(lineno)

    def test_missing_object_cannot_split(self):
        """Test that MissingObject cannot be split."""
        key = ('external-repo', 'missing-repo')
        missing = MissingObject(ExternalRepo, key)

        self.assertFalse(missing.can_split())
        with self.assertRaises(TypeError):
            missing.split()

    def test_missing_object_no_dependencies(self):
        """Test that MissingObject has no dependencies."""
        key = ('target', 'missing-target')
        missing = MissingObject(Target, key)

        deps = missing.dependency_keys()
        self.assertEqual(deps, ())


class TestResolver(unittest.TestCase):
    """Test the Resolver class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_data_path = Path(__file__).parent / 'data' / 'samples'

        # Create a mock namespace with some objects
        self.namespace = Mock(spec=Namespace)
        self.namespace._ns = {
            ('tag', 'existing-tag'): Tag(name='existing-tag', type='tag'),
            ('user', 'existing-user'): User(name='existing-user', type='user'),
        }
        self.namespace.get = self.namespace._ns.get

        self.resolver = Resolver(self.namespace)

    def test_resolver_initialization(self):
        """Test resolver initialization."""
        self.assertEqual(self.resolver.namespace, self.namespace)
        self.assertEqual(self.resolver._missing, {})

    def test_resolve_existing_object(self):
        """Test resolving an object that exists in the namespace."""
        key = ('tag', 'existing-tag')
        obj = self.resolver.resolve(key)

        self.assertIsInstance(obj, Tag)
        self.assertEqual(obj.name, 'existing-tag')
        self.assertEqual(obj.key(), key)

    def test_resolve_missing_object(self):
        """Test resolving an object that doesn't exist in the namespace."""
        key = ('tag', 'missing-tag')
        obj = self.resolver.resolve(key)

        self.assertIsInstance(obj, MissingObject)
        self.assertEqual(obj.key(), key)
        self.assertEqual(obj.name, 'missing-tag')

    def test_resolve_caches_missing_objects(self):
        """Test that missing objects are cached in created dict."""
        key = ('user', 'missing-user')

        # First resolution
        obj1 = self.resolver.resolve(key)
        self.assertIsInstance(obj1, MissingObject)

        # Second resolution should return same object
        obj2 = self.resolver.resolve(key)
        self.assertIs(obj1, obj2)

        # Should be in created dict
        self.assertIn(key, self.resolver._missing)
        self.assertIs(self.resolver._missing[key], obj1)

    def test_clear_removes_created_objects(self):
        """Test that clear() removes all created objects."""
        # Create some missing objects
        key1 = ('tag', 'missing-tag')
        key2 = ('user', 'missing-user')

        self.resolver.resolve(key1)
        self.resolver.resolve(key2)

        self.assertEqual(len(self.resolver._missing), 2)

        # Clear should remove them
        self.resolver.clear()
        self.assertEqual(len(self.resolver._missing), 0)

    def test_can_split_key_existing_object(self):
        """Test can_split_key with an existing object."""
        # Tag objects can be split
        key = ('tag', 'existing-tag')
        can_split = self.resolver.can_split_key(key)
        self.assertTrue(can_split)

    def test_can_split_key_missing_object(self):
        """Test can_split_key with a missing object."""
        # MissingObject cannot be split
        key = ('tag', 'missing-tag')
        can_split = self.resolver.can_split_key(key)
        self.assertFalse(can_split)

    def test_split_key_existing_object(self):
        """Test split_key with an existing object."""
        key = ('tag', 'existing-tag')
        split_obj = self.resolver.split_key(key)

        self.assertIsInstance(split_obj, Tag)
        self.assertEqual(split_obj.name, 'existing-tag')
        # Split object should have minimal data
        self.assertEqual(split_obj.arches, [])

    def test_split_key_missing_object(self):
        """Test split_key with a missing object."""
        key = ('tag', 'missing-tag')
        with self.assertRaises(TypeError):
            self.resolver.split_key(key)

    def test_report_returns_created_missing_objects(self):
        """Test that report() returns missing objects that were created."""
        # Create some missing objects
        key1 = ('tag', 'missing-tag')
        key2 = ('user', 'missing-user')

        self.resolver.resolve(key1)
        self.resolver.resolve(key2)

        report = self.resolver.report()

        self.assertIsInstance(report, Report)
        self.assertEqual(len(report.missing), 2)
        self.assertIn(key1, report.missing)
        self.assertIn(key2, report.missing)

    def test_report_empty_when_no_missing_objects(self):
        """Test that report() returns empty list when no missing objects created."""
        report = self.resolver.report()

        self.assertIsInstance(report, Report)
        self.assertEqual(report.missing, {})

    def test_resolve_with_none_namespace(self):
        """Test resolver behavior with None namespace."""

        with self.assertRaises(ValueError):
            Resolver(None)


class TestResolverIntegration(unittest.TestCase):
    """Test resolver integration with real namespace and models."""

    def setUp(self):
        """Set up test fixtures with real namespace."""
        self.test_data_path = Path(__file__).parent / 'data' / 'samples'

        # Create a real namespace with some test data
        self.namespace = Namespace()

        # Add some test objects
        tag_data = {'name': 'test-tag', 'type': 'tag', 'arches': ['x86_64']}
        user_data = {'name': 'test-user', 'type': 'user', 'enabled': True}

        self.namespace.add(Tag.from_dict(tag_data))
        self.namespace.add(User.from_dict(user_data))

        self.resolver = Resolver(self.namespace)

    def test_resolve_with_real_namespace(self):
        """Test resolving objects from a real namespace."""
        # Test resolving existing object
        key = ('tag', 'test-tag')
        obj = self.resolver.resolve(key)

        self.assertIsInstance(obj, Tag)
        self.assertEqual(obj.name, 'test-tag')
        self.assertEqual(obj.arches, ['x86_64'])

    def test_resolve_missing_with_real_namespace(self):
        """Test resolving missing objects with real namespace."""
        key = ('tag', 'missing-tag')
        obj = self.resolver.resolve(key)

        self.assertIsInstance(obj, MissingObject)
        self.assertEqual(obj.key(), key)

    def test_dependency_resolution_workflow(self):
        """Test a typical dependency resolution workflow."""
        # Create a tag that depends on a missing parent
        tag_data = {
            'name': 'child-tag',
            'type': 'tag',
            'inheritance': [{'name': 'parent-tag', 'priority': 10}]
        }
        child_tag = Tag.from_dict(tag_data)
        self.namespace.add(child_tag)

        # Resolve the child tag
        child_key = ('tag', 'child-tag')
        resolved_child = self.resolver.resolve(child_key)
        self.assertIsInstance(resolved_child, Tag)

        # Resolve the missing parent
        parent_key = ('tag', 'parent-tag')
        resolved_parent = self.resolver.resolve(parent_key)
        self.assertIsInstance(resolved_parent, MissingObject)

        # Check the report
        report = self.resolver.report()
        self.assertEqual(len(report.missing), 1)
        self.assertIn(parent_key, report.missing)


# The end.

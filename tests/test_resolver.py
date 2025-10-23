"""
koji-habitude - test_resolver

Unit tests for koji_habitude.resolver module.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated

from unittest import TestCase
from pathlib import Path
from unittest.mock import Mock

from koji_habitude.resolver import Resolver, Reference, ResolverReport
from koji_habitude.namespace import Namespace
from koji_habitude.models import Tag, User, ExternalRepo, Target
from koji_habitude.models import CoreObject


class TestReference(TestCase):
    """Test the Reference placeholder class."""

    def test_missing_object_creation(self):
        """Test creating a Reference with a key."""
        key = ('tag', 'missing-tag')
        missing = Reference(Tag, key)

        self.assertEqual(missing.typename, 'reference')
        self.assertEqual(missing.name, 'missing-tag')
        self.assertEqual(missing.yaml_type, 'tag')
        self.assertEqual(missing.key(), key)

    def test_missing_object_no_dependencies(self):
        """Test that Reference has no dependencies."""
        key = ('target', 'missing-target')
        missing = Reference(Target, key)

        deps = missing.dependency_keys()
        self.assertEqual(deps, ())


class TestResolver(TestCase):
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
        self.namespace.get_type.return_value = CoreObject

        self.resolver = Resolver(self.namespace)

    def test_resolver_initialization(self):
        """Test resolver initialization."""
        self.assertEqual(self.resolver.namespace, self.namespace)
        self.assertEqual(self.resolver._references, {})

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

        self.assertIsInstance(obj, Reference)
        self.assertEqual(obj.key(), key)
        self.assertEqual(obj.name, 'missing-tag')

    def test_resolve_caches_missing_objects(self):
        """Test that missing objects are cached in created dict."""
        key = ('user', 'missing-user')

        # First resolution
        obj1 = self.resolver.resolve(key)
        self.assertIsInstance(obj1, Reference)

        # Second resolution should return same object
        obj2 = self.resolver.resolve(key)
        self.assertIs(obj1, obj2)

        # Should be in created dict
        self.assertIn(key, self.resolver._references)
        self.assertIs(self.resolver._references[key], obj1)

    def test_clear_removes_created_objects(self):
        """Test that clear() removes all created objects."""
        # Create some missing objects
        key1 = ('tag', 'missing-tag')
        key2 = ('user', 'missing-user')

        self.resolver.resolve(key1)
        self.resolver.resolve(key2)

        self.assertEqual(len(self.resolver._references), 2)

        # Clear should remove them
        self.resolver.clear()
        self.assertEqual(len(self.resolver._references), 0)

    def test_report_returns_created_missing_objects(self):
        """Test that report() returns missing objects that were created."""
        # Create some missing objects
        key1 = ('tag', 'missing-tag')
        key2 = ('user', 'missing-user')

        self.resolver.resolve(key1)
        self.resolver.resolve(key2)

        report = self.resolver.report()

        self.assertIsInstance(report, ResolverReport)
        self.assertEqual(len(report.phantoms), 2)
        self.assertIn(key1, report.phantoms)
        self.assertIn(key2, report.phantoms)

    def test_report_empty_when_no_missing_objects(self):
        """Test that report() returns empty list when no missing objects created."""
        report = self.resolver.report()

        self.assertIsInstance(report, ResolverReport)
        self.assertEqual(report.phantoms, {})

    def test_resolve_with_none_namespace(self):
        """Test resolver behavior with None namespace."""

        with self.assertRaises(ValueError):
            Resolver(None)


class TestResolverIntegration(TestCase):
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

        self.assertIsInstance(obj, Reference)
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
        self.assertIsInstance(resolved_parent, Reference)

        # Check the report
        report = self.resolver.report()
        self.assertEqual(len(report.phantoms), 1)
        self.assertIn(parent_key, report.phantoms)


# The end.

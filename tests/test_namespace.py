"""
koji-habitude - test_namespace

Unit tests for koji_habitude.namespace module.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

import logging
import unittest
from unittest.mock import Mock, patch
from pathlib import Path

from koji_habitude.namespace import (
    add_into, Redefine, NamespaceRedefine, Namespace, TemplateNamespace
)
from koji_habitude.templates import Template, TemplateCall
from koji_habitude.models import Tag, ExternalRepo, CORE_MODELS


class MockObject:
    """Mock object for testing add_into function."""

    def __init__(self, name, filename="test.yaml", lineno=1):
        self.name = name
        self.filename = filename
        self.lineno = lineno

    def filepos(self):
        return f"{self.filename}:{self.lineno}"

    def __eq__(self, other):
        return isinstance(other, MockObject) and self.name == other.name


class TestAddInto(unittest.TestCase):
    """Test cases for the add_into helper function."""

    def setUp(self):
        """Set up test fixtures."""

        self.test_dict = {}
        self.mock_obj1 = MockObject("test1", "file1.yaml", 10)
        self.mock_obj2 = MockObject("test2", "file2.yaml", 20)
        self.mock_obj1_duplicate = MockObject("test1", "file3.yaml", 30)

    def test_add_into_empty_dict(self):
        """Test adding to an empty dictionary."""

        add_into(self.test_dict, "key1", self.mock_obj1)

        self.assertEqual(len(self.test_dict), 1)
        self.assertIs(self.test_dict["key1"], self.mock_obj1)

    def test_add_into_new_key(self):
        """Test adding a new key to existing dictionary."""

        self.test_dict["existing"] = self.mock_obj1
        add_into(self.test_dict, "new_key", self.mock_obj2)

        self.assertEqual(len(self.test_dict), 2)
        self.assertIs(self.test_dict["existing"], self.mock_obj1)
        self.assertIs(self.test_dict["new_key"], self.mock_obj2)

    def test_add_into_same_object(self):
        """Test adding the same object instance (should be no-op)."""

        add_into(self.test_dict, "key1", self.mock_obj1)
        original_len = len(self.test_dict)

        # Adding the same object instance should not raise error or change dict
        add_into(self.test_dict, "key1", self.mock_obj1)

        self.assertEqual(len(self.test_dict), original_len)
        self.assertIs(self.test_dict["key1"], self.mock_obj1)

    def test_add_into_redefine_error_default(self):
        """Test that redefinition raises error by default."""

        add_into(self.test_dict, "key1", self.mock_obj1)

        with self.assertRaises(NamespaceRedefine) as context:
            add_into(self.test_dict, "key1", self.mock_obj1_duplicate)

        self.assertIn("Redefinition of key1", str(context.exception))
        self.assertIn("file1.yaml:10", str(context.exception))
        self.assertIn("file3.yaml:30", str(context.exception))

    def test_add_into_redefine_error_explicit(self):
        """Test explicit ERROR redefine behavior."""

        add_into(self.test_dict, "key1", self.mock_obj1)

        with self.assertRaises(NamespaceRedefine):
            add_into(self.test_dict, "key1", self.mock_obj1_duplicate,
                    redefine=Redefine.ERROR)

        # Original object should still be there
        self.assertIs(self.test_dict["key1"], self.mock_obj1)

    def test_add_into_redefine_ignore(self):
        """Test IGNORE redefine behavior."""

        add_into(self.test_dict, "key1", self.mock_obj1)

        # Should not raise error and should keep original
        add_into(self.test_dict, "key1", self.mock_obj1_duplicate,
                redefine=Redefine.IGNORE)

        self.assertIs(self.test_dict["key1"], self.mock_obj1)

    def test_add_into_redefine_allow(self):
        """Test ALLOW redefine behavior."""

        add_into(self.test_dict, "key1", self.mock_obj1)

        # Should replace with new object
        add_into(self.test_dict, "key1", self.mock_obj1_duplicate,
                redefine=Redefine.ALLOW)

        self.assertIs(self.test_dict["key1"], self.mock_obj1_duplicate)

    @patch('koji_habitude.namespace.default_logger')
    def test_add_into_redefine_ignore_warn(self, mock_logger):
        """Test IGNORE_WARN redefine behavior."""

        add_into(self.test_dict, "key1", self.mock_obj1)

        # Should warn but keep original
        add_into(self.test_dict, "key1", self.mock_obj1_duplicate,
                redefine=Redefine.IGNORE_WARN)

        self.assertIs(self.test_dict["key1"], self.mock_obj1)
        mock_logger.warning.assert_called_once()
        self.assertIn("Ignored redefinition", mock_logger.warning.call_args[0][0])

    @patch('koji_habitude.namespace.default_logger')
    def test_add_into_redefine_allow_warn(self, mock_logger):
        """Test ALLOW_WARN redefine behavior."""

        add_into(self.test_dict, "key1", self.mock_obj1)

        # Should warn and replace with new object
        add_into(self.test_dict, "key1", self.mock_obj1_duplicate,
                redefine=Redefine.ALLOW_WARN)

        self.assertIs(self.test_dict["key1"], self.mock_obj1_duplicate)
        mock_logger.warning.assert_called_once()
        self.assertIn("Redefined", mock_logger.warning.call_args[0][0])

    def test_add_into_custom_logger(self):
        """Test using a custom logger."""

        custom_logger = Mock(spec=logging.Logger)
        add_into(self.test_dict, "key1", self.mock_obj1)

        add_into(self.test_dict, "key1", self.mock_obj1_duplicate,
                redefine=Redefine.IGNORE_WARN, logger=custom_logger)

        custom_logger.warning.assert_called_once()
        self.assertIn("Ignored redefinition", custom_logger.warning.call_args[0][0])

    def test_add_into_various_key_types(self):
        """Test add_into with various key types."""

        # String key
        add_into(self.test_dict, "string_key", self.mock_obj1)

        # Tuple key (like namespace uses)
        add_into(self.test_dict, ("type", "name"), self.mock_obj2)

        # Integer key
        mock_obj3 = MockObject("test3")
        add_into(self.test_dict, 42, mock_obj3)

        self.assertEqual(len(self.test_dict), 3)
        self.assertIs(self.test_dict["string_key"], self.mock_obj1)
        self.assertIs(self.test_dict[("type", "name")], self.mock_obj2)
        self.assertIs(self.test_dict[42], mock_obj3)

    def test_add_into_none_key(self):
        """Test add_into with None as key."""

        add_into(self.test_dict, None, self.mock_obj1)

        self.assertEqual(len(self.test_dict), 1)
        self.assertIs(self.test_dict[None], self.mock_obj1)


class TestNamespaceInitAndGuards(unittest.TestCase):
    """Test cases for Namespace initialization and add/add_template method guards."""

    def test_namespace_default_initialization(self):
        """Test creating a Namespace with default parameters."""

        ns = Namespace()

        # Check default values
        self.assertEqual(ns.redefine, Redefine.ERROR)
        self.assertIsNotNone(ns.logger)

        # Check typemap has core models
        self.assertIn("tag", ns.typemap)
        self.assertIn("external-repo", ns.typemap)
        self.assertIn("user", ns.typemap)
        self.assertIn("target", ns.typemap)
        self.assertIn("host", ns.typemap)
        self.assertIn("group", ns.typemap)

        # Check templates are enabled by default
        self.assertIn("template", ns.typemap)
        self.assertIn(None, ns.typemap)  # TemplateCall fallback

        # Check internal storage is initialized
        self.assertEqual(len(ns._feedline), 0)
        self.assertEqual(len(ns._ns), 0)
        self.assertEqual(len(ns._templates), 0)

    def test_namespace_custom_initialization(self):
        """Test creating a Namespace with custom parameters."""

        custom_logger = Mock(spec=logging.Logger)
        custom_coretypes = [Tag, ExternalRepo]

        ns = Namespace(
            coretypes=custom_coretypes,
            enable_templates=False,
            redefine=Redefine.ALLOW,
            logger=custom_logger
        )

        # Check custom values
        self.assertEqual(ns.redefine, Redefine.ALLOW)
        self.assertIs(ns.logger, custom_logger)

        # Check only custom coretypes are in typemap
        self.assertIn("tag", ns.typemap)
        self.assertIn("external-repo", ns.typemap)
        self.assertNotIn("user", ns.typemap)
        self.assertNotIn("target", ns.typemap)

        # Check templates are disabled
        self.assertNotIn("template", ns.typemap)
        self.assertNotIn(None, ns.typemap)

    def test_namespace_templates_enabled(self):
        """Test that templates are properly configured when enabled."""

        ns = Namespace(enable_templates=True)

        self.assertIs(ns.typemap["template"], Template)
        self.assertIs(ns.typemap[None], TemplateCall)

    def test_namespace_templates_disabled(self):
        """Test that templates are not configured when disabled."""

        ns = Namespace(enable_templates=False)

        self.assertNotIn("template", ns.typemap)
        self.assertNotIn(None, ns.typemap)

    def test_add_valid_core_object(self):
        """Test adding a valid core object to namespace."""

        ns = Namespace()
        tag_data = {'type': 'tag', 'name': 'test-tag'}
        tag_obj = Tag(tag_data)

        # Should not raise any exception
        ns.add(tag_obj)

        # Check object was added to namespace storage
        expected_key = ('tag', 'test-tag')
        self.assertIn(expected_key, ns._ns)
        self.assertIs(ns._ns[expected_key], tag_obj)

    def test_add_template_guard_rejects_template(self):
        """Test that add() rejects Template objects."""

        ns = Namespace()
        template_data = {'type': 'template', 'name': 'test-template', 'content': 'test'}
        template_obj = Template(template_data)

        with self.assertRaises(TypeError) as context:
            ns.add(template_obj)

        self.assertIn("Template cannot be directly added", str(context.exception))

    def test_add_template_guard_rejects_template_call(self):
        """Test that add() rejects TemplateCall objects."""

        ns = Namespace()
        call_data = {'type': 'custom-template', 'name': 'test-call'}
        call_obj = TemplateCall(call_data)

        with self.assertRaises(TypeError) as context:
            ns.add(call_obj)

        self.assertIn("TemplateCall cannot be directly added", str(context.exception))

    def test_add_template_valid_template(self):
        """Test adding a valid Template to namespace."""

        ns = Namespace()
        template_data = {'type': 'template', 'name': 'test-template', 'content': 'test'}
        template_obj = Template(template_data)

        # Should not raise any exception
        ns.add_template(template_obj)

        # Check template was added to template storage
        self.assertIn('test-template', ns._templates)
        self.assertIs(ns._templates['test-template'], template_obj)

    def test_add_template_guard_rejects_non_template(self):
        """Test that add_template() rejects non-Template objects."""

        ns = Namespace()
        tag_data = {'type': 'tag', 'name': 'test-tag'}
        tag_obj = Tag(tag_data)

        with self.assertRaises(TypeError) as context:
            ns.add_template(tag_obj)

        self.assertIn("add_template requires a Template instance", str(context.exception))

    def test_add_template_guard_rejects_template_call(self):
        """Test that add_template() rejects TemplateCall objects."""

        ns = Namespace()
        call_data = {'type': 'custom-template', 'name': 'test-call'}
        call_obj = TemplateCall(call_data)

        with self.assertRaises(TypeError) as context:
            ns.add_template(call_obj)

        self.assertIn("add_template requires a Template instance", str(context.exception))

    def test_add_duplicate_object_raises_error(self):
        """Test that adding duplicate objects raises NamespaceRedefine with ERROR mode."""

        ns = Namespace(redefine=Redefine.ERROR)
        tag_data = {'type': 'tag', 'name': 'test-tag'}
        tag_obj1 = Tag(tag_data)
        tag_obj2 = Tag(tag_data)

        # First add should succeed
        ns.add(tag_obj1)

        # Second add should raise error
        with self.assertRaises(NamespaceRedefine):
            ns.add(tag_obj2)

    def test_add_template_duplicate_raises_error(self):
        """Test that adding duplicate templates raises NamespaceRedefine with ERROR mode."""

        ns = Namespace(redefine=Redefine.ERROR)
        template_data1 = {'type': 'template', 'name': 'test-template', 'content': 'test1'}
        template_data2 = {'type': 'template', 'name': 'test-template', 'content': 'test2'}
        template_obj1 = Template(template_data1)
        template_obj2 = Template(template_data2)

        # First add should succeed
        ns.add_template(template_obj1)

        # Second add should raise error
        with self.assertRaises(NamespaceRedefine):
            ns.add_template(template_obj2)

    def test_add_same_object_instance_succeeds(self):
        """Test that adding the same object instance twice is allowed."""

        ns = Namespace(redefine=Redefine.ERROR)
        tag_data = {'type': 'tag', 'name': 'test-tag'}
        tag_obj = Tag(tag_data)

        # Both adds should succeed (same instance)
        ns.add(tag_obj)
        ns.add(tag_obj)  # Should not raise error

        # Should still only be one entry
        expected_key = ('tag', 'test-tag')
        self.assertIn(expected_key, ns._ns)
        self.assertIs(ns._ns[expected_key], tag_obj)

    def test_add_template_same_instance_succeeds(self):
        """Test that adding the same template instance twice is allowed."""

        ns = Namespace(redefine=Redefine.ERROR)
        template_data = {'type': 'template', 'name': 'test-template', 'content': 'test'}
        template_obj = Template(template_data)

        # Both adds should succeed (same instance)
        ns.add_template(template_obj)
        ns.add_template(template_obj)  # Should not raise error

        # Should still only be one entry
        self.assertIn('test-template', ns._templates)
        self.assertIs(ns._templates['test-template'], template_obj)


if __name__ == '__main__':
    unittest.main()


# The end.

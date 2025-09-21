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


if __name__ == '__main__':
    unittest.main()


# The end.

"""
koji-habitude - test_base

Unit tests for koji_habitude.models base classes.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

import unittest

from koji_habitude.models import BaseObject


class TestBaseModels(unittest.TestCase):
    """
    Test the base model classes.
    """

    def test_base_object_creation(self):
        """
        Test BaseObject creation with basic data.
        """

        data = {
            'type': 'test-type',
            'name': 'test-name',
            '__file__': 'test.yaml',
            '__line__': 42,
            '__trace__': [{'key': 'value'}]
        }

        obj = BaseObject.from_dict(data)

        self.assertEqual(obj.typename, 'object')
        self.assertEqual(obj.yaml_type, 'test-type')
        self.assertEqual(obj.name, 'test-name')
        self.assertEqual(obj.filename, 'test.yaml')
        self.assertEqual(obj.lineno, 42)
        self.assertEqual(obj.trace, [{'key': 'value'}])
        self.assertEqual(obj.data, data)

    def test_base_object_key_method(self):
        """
        Test the key() method returns correct tuple.
        """

        data = {'type': 'test-type', 'name': 'test-name'}
        obj = BaseObject.from_dict(data)

        key = obj.key()
        self.assertEqual(key, ('test-type', 'test-name'))

    def test_base_object_filepos_method(self):
        """
        Test the filepos() method returns correct tuple.
        """

        data = {
            'type': 'test-type',
            'name': 'test-name',
            '__file__': 'test.yaml',
            '__line__': 42
        }
        obj = BaseObject.from_dict(data)

        filepos = obj.filepos()
        self.assertEqual(filepos, ('test.yaml', 42))

    def test_base_object_can_split(self):
        """
        Test that BaseObject cannot be split.
        """

        data = {'type': 'test-type', 'name': 'test-name'}
        obj = BaseObject.from_dict(data)

        self.assertFalse(obj.can_split())

    def test_base_object_split_raises_error(self):
        """
        Test that BaseObject.split() raises TypeError.
        """

        data = {'type': 'test-type', 'name': 'test-name'}
        obj = BaseObject.from_dict(data)

        with self.assertRaises(TypeError) as context:
            obj.split()

        self.assertIn('Cannot split object', str(context.exception))

    def test_base_object_dependency_keys(self):
        """
        Test that BaseObject has no dependencies.
        """

        data = {'type': 'test-type', 'name': 'test-name'}
        obj = BaseObject.from_dict(data)

        deps = obj.dependency_keys()
        self.assertEqual(deps, ())

    def test_base_object_repr(self):
        """
        Test the string representation of BaseObject.
        """

        data = {'type': 'test-type', 'name': 'test-name'}
        obj = BaseObject.from_dict(data)

        repr_str = repr(obj)
        self.assertEqual(repr_str, '<CoreObject(test-name)>')

    def test_raw_object_alias(self):
        """
        Test that BaseObject is an alias for BaseObject.
        """

        data = {'type': 'test-type', 'name': 'test-name'}
        obj = BaseObject.from_dict(data)

        self.assertIsInstance(obj, BaseObject)
        self.assertEqual(obj.typename, 'object')


# The end.

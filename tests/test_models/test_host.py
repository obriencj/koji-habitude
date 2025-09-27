"""
koji-habitude - test_host

Unit tests for koji_habitude.models.Host.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

import unittest

from koji_habitude.models import Host


class TestHostModel(unittest.TestCase):
    """
    Test the Host model.
    """

    def test_host_creation_with_defaults(self):
        """
        Test Host creation with default values.
        """

        data = {'type': 'host', 'name': 'test-host'}
        host = Host.from_dict(data)

        self.assertEqual(host.typename, 'host')
        self.assertEqual(host.name, 'test-host')
        self.assertEqual(host.arches, [])
        self.assertEqual(host.capacity, None)
        self.assertTrue(host.enabled)
        self.assertEqual(host.description, None)
        self.assertEqual(host.channels, [])
        self.assertTrue(host.can_split())

    def test_host_creation_with_all_fields(self):
        """
        Test Host creation with all fields specified.
        """

        data = {
            'type': 'host',
            'name': 'test-host',
            'arches': ['x86_64', 'i686'],
            'capacity': 2.5,
            'enabled': False,
            'description': 'Test build host',
            'channels': ['default', 'build']
        }
        host = Host.from_dict(data)

        self.assertEqual(host.arches, ['x86_64', 'i686'])
        self.assertEqual(host.capacity, 2.5)
        self.assertFalse(host.enabled)
        self.assertEqual(host.description, 'Test build host')
        self.assertEqual(host.channels, ['default', 'build'])

    def test_host_split(self):
        """
        Test Host splitting functionality.
        """

        data = {
            'type': 'host',
            'name': 'test-host',
            'arches': ['x86_64'],
            'capacity': 2.0,
            'enabled': True,
            'description': 'Test host',
            'channels': ['default']
        }
        host = Host.from_dict(data)

        split_host = host.split()
        self.assertIsInstance(split_host, Host)
        self.assertEqual(split_host.name, 'test-host')
        self.assertEqual(split_host.arches, ['x86_64'])
        self.assertEqual(split_host.capacity, 2.0)
        self.assertTrue(split_host.enabled)
        self.assertEqual(split_host.description, 'Test host')
        # Channels should not be included in split (dependency data)
        self.assertEqual(split_host.channels, [])

    def test_host_dependency_keys(self):
        """
        Test Host dependency resolution.
        """

        data = {
            'type': 'host',
            'name': 'test-host',
            'channels': ['channel1', 'channel2']
        }
        host = Host.from_dict(data)

        deps = host.dependency_keys()
        expected = [('channel', 'channel1'), ('channel', 'channel2')]
        self.assertEqual(deps, expected)

    def test_host_dependency_keys_empty(self):
        """
        Test Host dependency resolution with no channels.
        """

        data = {'type': 'host', 'name': 'test-host'}
        host = Host.from_dict(data)

        deps = host.dependency_keys()
        self.assertEqual(deps, [])


# The end.

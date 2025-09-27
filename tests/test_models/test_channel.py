"""
koji-habitude - test_channel

Unit tests for koji_habitude.models.Channel.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

import unittest

from koji_habitude.models import Channel


class TestChannelModel(unittest.TestCase):
    """
    Test the Channel model.
    """

    def test_channel_creation_with_defaults(self):
        """
        Test Channel creation with default values.
        """

        data = {'type': 'channel', 'name': 'test-channel'}
        channel = Channel.from_dict(data)

        self.assertEqual(channel.typename, 'channel')
        self.assertEqual(channel.name, 'test-channel')
        self.assertEqual(channel.hosts, [])
        self.assertTrue(channel.can_split())

    def test_channel_creation_with_hosts(self):
        """
        Test Channel creation with hosts list.
        """

        data = {
            'type': 'channel',
            'name': 'test-channel',
            'hosts': ['host1', 'host2', 'host3']
        }
        channel = Channel.from_dict(data)

        self.assertEqual(channel.hosts, ['host1', 'host2', 'host3'])

    def test_channel_dependency_keys(self):
        """
        Test Channel dependency resolution.
        """

        data = {
            'type': 'channel',
            'name': 'test-channel',
            'hosts': ['host1', 'host2']
        }
        channel = Channel.from_dict(data)

        deps = channel.dependency_keys()
        expected = [('host', 'host1'), ('host', 'host2')]
        self.assertEqual(deps, expected)

    def test_channel_dependency_keys_empty(self):
        """
        Test Channel dependency resolution with no hosts.
        """

        data = {'type': 'channel', 'name': 'test-channel'}
        channel = Channel.from_dict(data)

        deps = channel.dependency_keys()
        self.assertEqual(deps, [])


# The end.

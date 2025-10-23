"""
koji-habitude - test_processor_models.test_channel

Unit tests for processor integration with channel models and change reporting.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

from unittest import TestCase
from unittest.mock import Mock

from koji_habitude.models import Channel
from koji_habitude.processor import Processor, ProcessorState, ProcessorSummary

from . import (
    MulticallMocking,
    create_empty_resolver,
    create_solver_with_objects,
    create_test_koji_session,
)


def create_test_channel(name: str, description: str = None, hosts: list = None,
                       exact_hosts: bool = False) -> Channel:
    """
    Create a test channel with the specified parameters.

    Args:
        name: Channel name
        description: Channel description (default None)
        hosts: List of host names (default empty list)
        exact_hosts: Whether to use exact host matching (default False)

    Returns:
        Channel object for testing
    """
    return Channel(
        name=name,
        description=description,
        hosts=hosts or [],
        exact_hosts=exact_hosts,
        filename='test.yaml',
        lineno=1
    )


class TestProcessorChannelBehavior(MulticallMocking, TestCase):

    def test_channel_creation(self):
        """Test creating a new channel with basic settings."""
        channel = create_test_channel('new-channel', description='Test channel')
        solver = create_solver_with_objects([channel])
        mock_session = create_test_koji_session()

        get_channel_mock = Mock()
        get_channel_mock.return_value = None

        list_hosts_mock = Mock()
        list_hosts_mock.return_value = []

        create_mock = Mock()
        create_mock.return_value = None

        self.queue_client_response('getChannel', get_channel_mock)
        self.queue_client_response('listHosts', list_hosts_mock)
        self.queue_client_response('createChannel', create_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_channel_mock.assert_called_once_with('new-channel', strict=False)
        list_hosts_mock.assert_not_called()
        create_mock.assert_called_once_with('new-channel', 'Test channel')

    def test_channel_creation_without_description(self):
        """Test creating a new channel without description."""
        channel = create_test_channel('new-channel')
        solver = create_solver_with_objects([channel])
        mock_session = create_test_koji_session()

        get_channel_mock = Mock()
        get_channel_mock.return_value = None

        list_hosts_mock = Mock()
        list_hosts_mock.return_value = []

        create_mock = Mock()
        create_mock.return_value = None

        self.queue_client_response('getChannel', get_channel_mock)
        self.queue_client_response('listHosts', list_hosts_mock)
        self.queue_client_response('createChannel', create_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_channel_mock.assert_called_once_with('new-channel', strict=False)
        list_hosts_mock.assert_not_called()
        create_mock.assert_called_once_with('new-channel', None)

    def test_channel_creation_with_hosts(self):
        """Test creating a channel with hosts."""
        channel = create_test_channel('new-channel', hosts=['host1', 'host2'])
        solver = create_solver_with_objects([channel])
        mock_session = create_test_koji_session()

        get_channel_mock = Mock()
        get_channel_mock.return_value = None

        list_hosts_mock = Mock()
        list_hosts_mock.return_value = []

        create_mock = Mock()
        create_mock.return_value = None

        add_host1_mock = Mock()
        add_host1_mock.return_value = None

        add_host2_mock = Mock()
        add_host2_mock.return_value = None

        self.queue_client_response('getChannel', get_channel_mock)
        self.queue_client_response('listHosts', list_hosts_mock)
        self.queue_client_response('createChannel', create_mock)
        self.queue_client_response('addHostToChannel', add_host1_mock)
        self.queue_client_response('addHostToChannel', add_host2_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_channel_mock.assert_called_once_with('new-channel', strict=False)
        list_hosts_mock.assert_not_called()
        create_mock.assert_called_once_with('new-channel', None)
        add_host1_mock.assert_called_once_with('host1', 'new-channel')
        add_host2_mock.assert_called_once_with('host2', 'new-channel')

    def test_channel_update_description(self):
        """Test updating an existing channel's description."""
        channel = create_test_channel('existing-channel', description='New description')
        solver = create_solver_with_objects([channel])
        mock_session = create_test_koji_session()

        # Mock the getChannel call to return existing channel with different description
        get_channel_mock = Mock()
        get_channel_mock.return_value = {
            'id': 100,
            'name': 'existing-channel',
            'description': 'Old description'
        }

        list_hosts_mock = Mock()
        list_hosts_mock.return_value = []

        edit_mock = Mock()
        edit_mock.return_value = None

        self.queue_client_response('getChannel', get_channel_mock)
        self.queue_client_response('listHosts', list_hosts_mock)
        self.queue_client_response('editChannel', edit_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_channel_mock.assert_called_once_with('existing-channel', strict=False)
        list_hosts_mock.assert_called_once_with(channelID='existing-channel')
        edit_mock.assert_called_once_with('existing-channel', description='New description')

    def test_channel_add_missing_hosts(self):
        """Test adding hosts to a channel that doesn't have them."""
        channel = create_test_channel('existing-channel', hosts=['host1', 'host2'])
        solver = create_solver_with_objects([channel])
        mock_session = create_test_koji_session()

        # Mock the getChannel call to return existing channel
        get_channel_mock = Mock()
        get_channel_mock.return_value = {
            'id': 100,
            'name': 'existing-channel',
            'description': 'Test channel'
        }

        list_hosts_mock = Mock()
        list_hosts_mock.return_value = []  # No hosts currently

        add_host1_mock = Mock()
        add_host1_mock.return_value = None

        add_host2_mock = Mock()
        add_host2_mock.return_value = None

        self.queue_client_response('getChannel', get_channel_mock)
        self.queue_client_response('listHosts', list_hosts_mock)
        self.queue_client_response('addHostToChannel', add_host1_mock)
        self.queue_client_response('addHostToChannel', add_host2_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_channel_mock.assert_called_once_with('existing-channel', strict=False)
        list_hosts_mock.assert_called_once_with(channelID='existing-channel')
        add_host1_mock.assert_called_once_with('host1', 'existing-channel')
        add_host2_mock.assert_called_once_with('host2', 'existing-channel')

    def test_channel_remove_extra_hosts_with_exact_hosts(self):
        """Test removing hosts from a channel when exact_hosts=True."""
        channel = create_test_channel('existing-channel', hosts=['host1'], exact_hosts=True)
        solver = create_solver_with_objects([channel])
        mock_session = create_test_koji_session()

        # Mock the getChannel call to return existing channel with extra hosts
        get_channel_mock = Mock()
        get_channel_mock.return_value = {
            'id': 100,
            'name': 'existing-channel',
            'description': 'Test channel'
        }

        list_hosts_mock = Mock()
        list_hosts_mock.return_value = [
            {'name': 'host1'},
            {'name': 'extra-host'}  # Has extra host
        ]

        remove_host_mock = Mock()
        remove_host_mock.return_value = None

        self.queue_client_response('getChannel', get_channel_mock)
        self.queue_client_response('listHosts', list_hosts_mock)
        self.queue_client_response('removeHostFromChannel', remove_host_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_channel_mock.assert_called_once_with('existing-channel', strict=False)
        list_hosts_mock.assert_called_once_with(channelID='existing-channel')
        remove_host_mock.assert_called_once_with('extra-host', 'existing-channel')

    def test_channel_no_changes_needed(self):
        """Test channel that already matches desired state."""
        channel = create_test_channel('existing-channel', description='Test description',
                                     hosts=['host1', 'host2'])
        solver = create_solver_with_objects([channel])
        mock_session = create_test_koji_session()

        # Mock the getChannel call to return channel that already matches desired state
        get_channel_mock = Mock()
        get_channel_mock.return_value = {
            'id': 100,
            'name': 'existing-channel',
            'description': 'Test description'  # Already matches
        }

        list_hosts_mock = Mock()
        list_hosts_mock.return_value = [
            {'name': 'host1'},  # Already has host1
            {'name': 'host2'}   # Already has host2
        ]

        self.queue_client_response('getChannel', get_channel_mock)
        self.queue_client_response('listHosts', list_hosts_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_channel_mock.assert_called_once_with('existing-channel', strict=False)
        list_hosts_mock.assert_called_once_with(channelID='existing-channel')

    def test_channel_update_description_from_none(self):
        """Test updating a channel that has no description to have one."""
        channel = create_test_channel('existing-channel', description='New description')
        solver = create_solver_with_objects([channel])
        mock_session = create_test_koji_session()

        # Mock the getChannel call to return channel with no description
        get_channel_mock = Mock()
        get_channel_mock.return_value = {
            'id': 100,
            'name': 'existing-channel',
            'description': None  # No current description
        }

        list_hosts_mock = Mock()
        list_hosts_mock.return_value = []

        edit_mock = Mock()
        edit_mock.return_value = None

        self.queue_client_response('getChannel', get_channel_mock)
        self.queue_client_response('listHosts', list_hosts_mock)
        self.queue_client_response('editChannel', edit_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_channel_mock.assert_called_once_with('existing-channel', strict=False)
        list_hosts_mock.assert_called_once_with(channelID='existing-channel')
        edit_mock.assert_called_once_with('existing-channel', description='New description')

    def test_processor_summary_with_multiple_channels(self):
        """Test that the processor summary is correct with multiple channels."""
        channels = [
            create_test_channel('channel1', description='First channel'),
            create_test_channel('channel2', hosts=['host1'])
        ]
        solver = create_solver_with_objects(channels)
        mock_session = create_test_koji_session()

        # Mock getChannel calls to return None (channels don't exist)
        get_channel1_mock = Mock()
        get_channel1_mock.return_value = None

        get_channel2_mock = Mock()
        get_channel2_mock.return_value = None

        # Mock listHosts calls
        list_hosts1_mock = Mock()
        list_hosts1_mock.return_value = []

        list_hosts2_mock = Mock()
        list_hosts2_mock.return_value = []

        # Mock createChannel calls for channel creation
        create1_mock = Mock()
        create1_mock.return_value = None

        create2_mock = Mock()
        create2_mock.return_value = None

        # Mock addHostToChannel call for channel2
        add_host_mock = Mock()
        add_host_mock.return_value = None

        # Queue responses for both channels
        self.queue_client_response('getChannel', get_channel1_mock)
        self.queue_client_response('listHosts', list_hosts1_mock)
        self.queue_client_response('createChannel', create1_mock)

        self.queue_client_response('getChannel', get_channel2_mock)
        self.queue_client_response('listHosts', list_hosts2_mock)
        self.queue_client_response('createChannel', create2_mock)
        self.queue_client_response('addHostToChannel', add_host_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        summary = processor.run()
        self.assertIsInstance(summary, ProcessorSummary)
        self.assertEqual(summary.total_objects, 2)
        self.assertEqual(summary.steps_completed, 1)
        self.assertEqual(summary.state, ProcessorState.EXHAUSTED)

        # Verify all calls were made
        get_channel1_mock.assert_called_once_with('channel1', strict=False)
        get_channel2_mock.assert_called_once_with('channel2', strict=False)
        list_hosts1_mock.assert_not_called()
        list_hosts2_mock.assert_not_called()
        create1_mock.assert_called_once_with('channel1', 'First channel')
        create2_mock.assert_called_once_with('channel2', None)
        add_host_mock.assert_called_once_with('host1', 'channel2')


# The end.

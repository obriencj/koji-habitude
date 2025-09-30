"""
koji-habitude - test_processor_models.test_host

Unit tests for processor integration with host models and change reporting.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

from unittest import TestCase
from unittest.mock import Mock, call

from koji_habitude.models import Host
from koji_habitude.processor import (
    DiffOnlyProcessor,
    Processor,
    ProcessorState,
    ProcessorSummary,
)

from . import (
    MulticallMocking,
    create_empty_resolver,
    create_solver_with_objects,
    create_test_koji_session,
)


def create_test_host(name: str, arches: list = None, capacity: float = None,
                    enabled: bool = True, description: str = None,
                    channels: list = None, exact_channels: bool = False) -> Host:
    """
    Create a test host with the specified parameters.

    Args:
        name: Host name
        arches: List of architectures (default empty list)
        capacity: Host capacity (default 0.0)
        enabled: Whether host is enabled (default True)
        description: Host description (default empty string)
        channels: List of channels (default empty list)
        exact_channels: Whether to use exact channel matching (default False)

    Returns:
        Host object for testing
    """
    return Host(
        name=name,
        arches=arches or ['x86_64'],
        capacity=capacity,
        enabled=enabled,
        description=description,
        channels=channels or [],
        exact_channels=exact_channels,
        filename='test.yaml',
        lineno=1
    )


class TestProcessorHostBehavior(MulticallMocking, TestCase):

    def test_host_creation(self):
        """Test creating a new host with basic settings."""
        host = create_test_host('new-host', arches=['x86_64'], capacity=2.0,
                               description='Test host')
        solver = create_solver_with_objects([host])
        mock_session = create_test_koji_session()

        get_host_mock = Mock()
        get_host_mock.return_value = None

        create_mock = Mock()
        create_mock.return_value = None

        edit_host_mock = Mock()
        edit_host_mock.side_effect = [None, None, None]

        self.queue_client_response('getHost', get_host_mock)
        self.queue_client_response('createHost', create_mock)
        self.queue_client_response('editHost', edit_host_mock)
        self.queue_client_response('editHost', edit_host_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_host_mock.assert_called_once_with('new-host', strict=False)
        create_mock.assert_called_once()

        expected_calls = [
            call('new-host', capacity=2.0),
            call('new-host', description='Test host')
        ]
        edit_host_mock.assert_has_calls(expected_calls)

    def test_host_creation_with_channels(self):
        """Test creating a host with channels."""
        host = create_test_host('new-host', arches=['x86_64'], channels=['build', 'test'])
        solver = create_solver_with_objects([host])
        mock_session = create_test_koji_session()

        get_host_mock = Mock()
        get_host_mock.return_value = None

        create_mock = Mock()
        create_mock.return_value = None

        add_channel_mock = Mock()
        add_channel_mock.side_effect = [None, None]

        self.queue_client_response('getHost', get_host_mock)
        self.queue_client_response('createHost', create_mock)
        self.queue_client_response('addHostToChannel', add_channel_mock)
        self.queue_client_response('addHostToChannel', add_channel_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_host_mock.assert_called_once_with('new-host', strict=False)
        create_mock.assert_called_once()

        expected_calls = [
            call('new-host', 'build'),
            call('new-host', 'test')
        ]
        add_channel_mock.assert_has_calls(expected_calls)

    def test_host_update_arches(self):
        """Test updating an existing host's architectures."""
        host = create_test_host('existing-host', arches=['x86_64', 'aarch64'])
        solver = create_solver_with_objects([host])
        mock_session = create_test_koji_session()

        # Mock the getHost call to return existing host with different arches
        get_host_mock = Mock()
        get_host_mock.return_value = {
            'name': 'existing-host',
            'arches': 'x86_64',  # Currently only x86_64
            'capacity': 2.0,
            'enabled': True,
            'description': 'Test host',
            'channels': []
        }

        set_arches_mock = Mock()
        set_arches_mock.return_value = None

        self.queue_client_response('getHost', get_host_mock)
        self.queue_client_response('editHost', set_arches_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_host_mock.assert_called_once_with('existing-host', strict=False)
        set_arches_mock.assert_called_once_with('existing-host', arches='x86_64 aarch64')

    def test_host_update_capacity(self):
        """Test updating an existing host's capacity."""
        host = create_test_host('existing-host', capacity=4.0)
        solver = create_solver_with_objects([host])
        mock_session = create_test_koji_session()

        # Mock the getHost call to return existing host with different capacity
        get_host_mock = Mock()
        get_host_mock.return_value = {
            'name': 'existing-host',
            'arches': 'x86_64',
            'capacity': 2.0,  # Currently 2.0
            'enabled': True,
            'description': 'Test host',
            'channels': []
        }

        set_capacity_mock = Mock()
        set_capacity_mock.return_value = None

        self.queue_client_response('getHost', get_host_mock)
        self.queue_client_response('editHost', set_capacity_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_host_mock.assert_called_once_with('existing-host', strict=False)
        set_capacity_mock.assert_called_once_with('existing-host', capacity=4.0)

    def test_host_update_enabled_status(self):
        """Test updating an existing host's enabled status."""
        host = create_test_host('existing-host', enabled=False)
        solver = create_solver_with_objects([host])
        mock_session = create_test_koji_session()

        # Mock the getHost call to return existing host with different enabled status
        get_host_mock = Mock()
        get_host_mock.return_value = {
            'name': 'existing-host',
            'arches': 'x86_64',
            'capacity': 2.0,
            'enabled': True,  # Currently enabled
            'description': 'Test host',
            'channels': []
        }

        set_enabled_mock = Mock()
        set_enabled_mock.return_value = None

        self.queue_client_response('getHost', get_host_mock)
        self.queue_client_response('editHost', set_enabled_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_host_mock.assert_called_once_with('existing-host', strict=False)
        set_enabled_mock.assert_called_once_with('existing-host', enabled=False)

    def test_host_update_description(self):
        """Test updating an existing host's description."""
        host = create_test_host('existing-host', description='New description')
        solver = create_solver_with_objects([host])
        mock_session = create_test_koji_session()

        # Mock the getHost call to return existing host with different description
        get_host_mock = Mock()
        get_host_mock.return_value = {
            'name': 'existing-host',
            'arches': 'x86_64',
            'capacity': 2.0,
            'enabled': True,
            'description': 'Old description',  # Currently different
            'channels': []
        }

        set_description_mock = Mock()
        set_description_mock.return_value = None

        self.queue_client_response('getHost', get_host_mock)
        self.queue_client_response('editHost', set_description_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_host_mock.assert_called_once_with('existing-host', strict=False)
        set_description_mock.assert_called_once_with('existing-host', description='New description')

    def test_host_add_missing_channels(self):
        """Test adding channels to a host that doesn't have them."""
        host = create_test_host('existing-host', channels=['build', 'test'])
        solver = create_solver_with_objects([host])
        mock_session = create_test_koji_session()

        # Mock the getHost call to return existing host with no channels
        get_host_mock = Mock()
        get_host_mock.return_value = {
            'name': 'existing-host',
            'arches': 'x86_64',
            'capacity': 2.0,
            'enabled': True,
            'description': 'Test host',
            'channels': []  # No channels currently
        }

        add_channel1_mock = Mock()
        add_channel1_mock.return_value = None

        add_channel2_mock = Mock()
        add_channel2_mock.return_value = None

        self.queue_client_response('getHost', get_host_mock)
        self.queue_client_response('addHostToChannel', add_channel1_mock)
        self.queue_client_response('addHostToChannel', add_channel2_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_host_mock.assert_called_once_with('existing-host', strict=False)
        add_channel1_mock.assert_called_once_with('existing-host', 'build')
        add_channel2_mock.assert_called_once_with('existing-host', 'test')

    def test_host_remove_extra_channels_with_exact_channels(self):
        """Test removing channels from a host when exact_channels=True."""
        host = create_test_host('existing-host', channels=['build'], exact_channels=True)
        solver = create_solver_with_objects([host])
        mock_session = create_test_koji_session()

        # Mock the getHost call to return existing host with extra channels
        get_host_mock = Mock()
        get_host_mock.return_value = {
            'name': 'existing-host',
            'arches': 'x86_64',
            'capacity': 2.0,
            'enabled': True,
            'description': 'Test host',
            'channels': ['build', 'extra-channel']  # Has extra channel
        }

        remove_channel_mock = Mock()
        remove_channel_mock.return_value = None

        self.queue_client_response('getHost', get_host_mock)
        self.queue_client_response('removeHostFromChannel', remove_channel_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_host_mock.assert_called_once_with('existing-host', strict=False)
        remove_channel_mock.assert_called_once_with('existing-host', 'extra-channel')

    def test_host_no_changes_needed(self):
        """Test host that already matches desired state."""
        host = create_test_host('existing-host', arches=['x86_64'], capacity=2.0,
                               enabled=True, description='Test host', channels=['build'])
        solver = create_solver_with_objects([host])
        mock_session = create_test_koji_session()

        # Mock the getHost call to return host that already matches desired state
        get_host_mock = Mock()
        get_host_mock.return_value = {
            'name': 'existing-host',
            'arches': 'x86_64',  # Already matches
            'capacity': 2.0,  # Already matches
            'enabled': True,  # Already matches
            'description': 'Test host',  # Already matches
            'channels': ['build']  # Already matches
        }

        self.queue_client_response('getHost', get_host_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_host_mock.assert_called_once_with('existing-host', strict=False)

    def test_processor_summary_with_multiple_hosts(self):
        """Test that the processor summary is correct with multiple hosts."""
        hosts = [
            create_test_host('host1', arches=['x86_64'], capacity=2.0),
            create_test_host('host2', arches=['aarch64'], capacity=4.0, enabled=False)
        ]
        solver = create_solver_with_objects(hosts)
        mock_session = create_test_koji_session()

        # Mock getHost calls to return None (hosts don't exist)
        get_host1_mock = Mock()
        get_host1_mock.return_value = None

        get_host2_mock = Mock()
        get_host2_mock.return_value = None

        # Mock createHost calls for host creation
        create1_mock = Mock()
        create1_mock.return_value = None

        create2_mock = Mock()
        create2_mock.return_value = None

        edit1_mock = Mock()
        edit1_mock.side_effect = [None]

        edit2_mock = Mock()
        edit2_mock.side_effect = [None, None]

        # Queue responses for both hosts
        self.queue_client_response('getHost', get_host1_mock)
        self.queue_client_response('createHost', create1_mock)
        self.queue_client_response('editHost', edit1_mock)

        self.queue_client_response('getHost', get_host2_mock)
        self.queue_client_response('createHost', create2_mock)
        self.queue_client_response('editHost', edit2_mock)
        self.queue_client_response('editHost', edit2_mock)

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
        get_host1_mock.assert_called_once_with('host1', strict=False)
        get_host2_mock.assert_called_once_with('host2', strict=False)
        create1_mock.assert_called_once()
        create2_mock.assert_called_once()

        expected1_calls = [
            call('host1', capacity=2.0)
        ]
        edit1_mock.assert_has_calls(expected1_calls)

        expected2_calls = [
            call('host2', capacity=4.0),
            call('host2', enabled=False)
        ]
        edit2_mock.assert_has_calls(expected2_calls)

# The end.

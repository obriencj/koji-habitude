"""
koji-habitude - test_processor_models.test_archive_type

Unit tests for processor integration with archive type models and change reporting.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 4.5 Sonnet via Cursor
"""

from unittest import TestCase
from unittest.mock import Mock

from koji_habitude.models import ArchiveType
from koji_habitude.processor import (
    CompareOnlyProcessor,
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


def create_test_archive_type(name: str, extensions: list = None,
                             description: str = '', compression: str = None) -> ArchiveType:
    """
    Create a test archive type with the specified parameters.

    Args:
        name: Archive type name
        extensions: List of file extensions (default ['test'])
        description: Archive type description (default empty string)
        compression: Compression type ('tar' or 'zip', default None)

    Returns:
        ArchiveType object for testing
    """
    return ArchiveType(
        name=name,
        extensions=extensions or ['test'],
        description=description,
        compression=compression,
        filename='test.yaml',
        lineno=1
    )


class TestProcessorArchiveTypeBehavior(MulticallMocking, TestCase):

    def test_archive_type_creation_minimal(self):
        """Test creating a new archive type with minimal fields."""
        archive_type = create_test_archive_type('jar', extensions=['jar'])
        solver = create_solver_with_objects([archive_type])
        mock_session = create_test_koji_session()

        get_archive_types_mock = Mock()
        get_archive_types_mock.return_value = []  # Archive type doesn't exist

        add_archive_type_mock = Mock()
        add_archive_type_mock.return_value = None

        self.queue_client_response('getArchiveTypes', get_archive_types_mock)
        self.queue_client_response('addArchiveType', add_archive_type_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_archive_types_mock.assert_called_once_with()
        add_archive_type_mock.assert_called_once_with(
            name='jar',
            description='',
            extensions='jar',
            compression=None
        )

    def test_archive_type_creation_with_description(self):
        """Test creating an archive type with description."""
        archive_type = create_test_archive_type(
            'war',
            extensions=['war'],
            description='Web Application Archive'
        )
        solver = create_solver_with_objects([archive_type])
        mock_session = create_test_koji_session()

        get_archive_types_mock = Mock()
        get_archive_types_mock.return_value = []

        add_archive_type_mock = Mock()
        add_archive_type_mock.return_value = None

        self.queue_client_response('getArchiveTypes', get_archive_types_mock)
        self.queue_client_response('addArchiveType', add_archive_type_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_archive_types_mock.assert_called_once_with()
        add_archive_type_mock.assert_called_once_with(
            name='war',
            description='Web Application Archive',
            extensions='war',
            compression=None
        )

    def test_archive_type_creation_with_compression(self):
        """Test creating an archive type with compression."""
        archive_type = create_test_archive_type(
            'tar',
            extensions=['tar'],
            description='TAR archive',
            compression='tar'
        )
        solver = create_solver_with_objects([archive_type])
        mock_session = create_test_koji_session()

        get_archive_types_mock = Mock()
        get_archive_types_mock.return_value = []

        add_archive_type_mock = Mock()
        add_archive_type_mock.return_value = None

        self.queue_client_response('getArchiveTypes', get_archive_types_mock)
        self.queue_client_response('addArchiveType', add_archive_type_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_archive_types_mock.assert_called_once_with()
        add_archive_type_mock.assert_called_once_with(
            name='tar',
            description='TAR archive',
            extensions='tar',
            compression='tar'
        )

    def test_archive_type_creation_multiple_extensions(self):
        """Test creating an archive type with multiple extensions."""
        archive_type = create_test_archive_type(
            'tarball',
            extensions=['tar.gz', 'tgz', 'tar.bz2'],
            compression='tar'
        )
        solver = create_solver_with_objects([archive_type])
        mock_session = create_test_koji_session()

        get_archive_types_mock = Mock()
        get_archive_types_mock.return_value = []

        add_archive_type_mock = Mock()
        add_archive_type_mock.return_value = None

        self.queue_client_response('getArchiveTypes', get_archive_types_mock)
        self.queue_client_response('addArchiveType', add_archive_type_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_archive_types_mock.assert_called_once_with()
        # Extensions should be space-separated
        call_args = add_archive_type_mock.call_args
        self.assertEqual(call_args[1]['name'], 'tarball')
        # Check that extensions are space-separated (order may vary due to set)
        extensions_str = call_args[1]['extensions']
        extensions_list = extensions_str.split(' ')
        self.assertEqual(len(extensions_list), 3)
        self.assertIn('tar.gz', extensions_list)
        self.assertIn('tgz', extensions_list)
        self.assertIn('tar.bz2', extensions_list)

    def test_archive_type_no_changes_needed(self):
        """Test archive type that already exists."""
        archive_type = create_test_archive_type('jar', extensions=['jar'])
        solver = create_solver_with_objects([archive_type])
        mock_session = create_test_koji_session()

        # Mock getArchiveTypes to return existing archive type
        get_archive_types_mock = Mock()
        get_archive_types_mock.return_value = [{
            'id': 1,
            'name': 'jar',
            'description': '',
            'extensions': 'jar',
            'compression_type': None
        }]

        self.queue_client_response('getArchiveTypes', get_archive_types_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_archive_types_mock.assert_called_once_with()
        # Should not call addArchiveType since it already exists

    def test_processor_summary_with_multiple_archive_types(self):
        """Test that the processor summary is correct with multiple archive types."""
        archive_types = [
            create_test_archive_type('jar', extensions=['jar']),
            create_test_archive_type('war', extensions=['war'], description='Web Archive'),
            create_test_archive_type('tar', extensions=['tar'], compression='tar')
        ]
        solver = create_solver_with_objects(archive_types)
        mock_session = create_test_koji_session()

        # Mock getArchiveTypes calls to return empty (archive types don't exist)
        get_types1_mock = Mock()
        get_types1_mock.return_value = []

        get_types2_mock = Mock()
        get_types2_mock.return_value = []

        get_types3_mock = Mock()
        get_types3_mock.return_value = []

        # Mock addArchiveType calls for creation
        add_jar_mock = Mock()
        add_jar_mock.return_value = None

        add_war_mock = Mock()
        add_war_mock.return_value = None

        add_tar_mock = Mock()
        add_tar_mock.return_value = None

        # Queue responses for all archive types
        self.queue_client_response('getArchiveTypes', get_types1_mock)
        self.queue_client_response('addArchiveType', add_jar_mock)

        self.queue_client_response('getArchiveTypes', get_types2_mock)
        self.queue_client_response('addArchiveType', add_war_mock)

        self.queue_client_response('getArchiveTypes', get_types3_mock)
        self.queue_client_response('addArchiveType', add_tar_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        summary = processor.run()
        self.assertIsInstance(summary, ProcessorSummary)
        self.assertEqual(summary.total_objects, 3)
        self.assertEqual(summary.steps_completed, 1)
        self.assertEqual(summary.state, ProcessorState.EXHAUSTED)

        # Verify all calls were made
        get_types1_mock.assert_called_once_with()
        get_types2_mock.assert_called_once_with()
        get_types3_mock.assert_called_once_with()
        add_jar_mock.assert_called_once_with(
            name='jar', description='', extensions='jar', compression=None)
        add_war_mock.assert_called_once_with(
            name='war', description='Web Archive', extensions='war', compression=None)
        add_tar_mock.assert_called_once_with(
            name='tar', description='', extensions='tar', compression='tar')

    def test_archive_type_mixed_new_and_existing(self):
        """Test processing a mix of new and existing archive types."""
        archive_types = [
            create_test_archive_type('jar', extensions=['jar']),  # Already exists
            create_test_archive_type('custom', extensions=['custom'], description='Custom type'),  # New
        ]
        solver = create_solver_with_objects(archive_types)
        mock_session = create_test_koji_session()

        # Mock jar as existing
        get_jar_mock = Mock()
        get_jar_mock.return_value = [{
            'id': 1,
            'name': 'jar',
            'description': '',
            'extensions': 'jar'
        }]

        # Mock custom as not existing
        get_custom_mock = Mock()
        get_custom_mock.return_value = []

        add_custom_mock = Mock()
        add_custom_mock.return_value = None

        # Queue responses
        self.queue_client_response('getArchiveTypes', get_jar_mock)
        self.queue_client_response('getArchiveTypes', get_custom_mock)
        self.queue_client_response('addArchiveType', add_custom_mock)

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

        # Verify jar was checked but not created
        get_jar_mock.assert_called_once_with()

        # Verify custom was created
        get_custom_mock.assert_called_once_with()
        add_custom_mock.assert_called_once_with(
            name='custom', description='Custom type', extensions='custom', compression=None)


# The end.

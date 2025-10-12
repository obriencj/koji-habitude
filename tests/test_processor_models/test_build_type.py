"""
koji-habitude - test_processor_models.test_build_type

Unit tests for processor integration with build type models and change reporting.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 4.5 Sonnet via Cursor
"""

from unittest import TestCase
from unittest.mock import Mock

from koji_habitude.models import BuildType
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


def create_test_build_type(name: str) -> BuildType:
    """
    Create a test build type with the specified parameters.

    Args:
        name: Build type name

    Returns:
        BuildType object for testing
    """
    return BuildType(
        name=name,
        filename='test.yaml',
        lineno=1
    )


class TestProcessorBuildTypeBehavior(MulticallMocking, TestCase):

    def test_build_type_creation(self):
        """Test creating a new build type."""
        build_type = create_test_build_type('rpm')
        solver = create_solver_with_objects([build_type])
        mock_session = create_test_koji_session()

        list_btypes_mock = Mock()
        list_btypes_mock.return_value = []  # Build type doesn't exist

        add_btype_mock = Mock()
        add_btype_mock.return_value = None

        self.queue_client_response('listBTypes', list_btypes_mock)
        self.queue_client_response('addBType', add_btype_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        list_btypes_mock.assert_called_once_with(query={'name': 'rpm'})
        add_btype_mock.assert_called_once_with('rpm')

    def test_build_type_no_changes_needed(self):
        """Test build type that already exists."""
        build_type = create_test_build_type('maven')
        solver = create_solver_with_objects([build_type])
        mock_session = create_test_koji_session()

        # Mock listBTypes to return existing build type
        list_btypes_mock = Mock()
        list_btypes_mock.return_value = [{'id': 1, 'name': 'maven'}]

        self.queue_client_response('listBTypes', list_btypes_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        list_btypes_mock.assert_called_once_with(query={'name': 'maven'})
        # Should not call addBType

    def test_processor_summary_with_multiple_build_types(self):
        """Test that the processor summary is correct with multiple build types."""
        build_types = [
            create_test_build_type('rpm'),
            create_test_build_type('maven'),
            create_test_build_type('image')
        ]
        solver = create_solver_with_objects(build_types)
        mock_session = create_test_koji_session()

        # Mock listBTypes calls to return empty (build types don't exist)
        list_rpm_mock = Mock()
        list_rpm_mock.return_value = []

        list_maven_mock = Mock()
        list_maven_mock.return_value = []

        list_image_mock = Mock()
        list_image_mock.return_value = []

        # Mock addBType calls for creation
        add_rpm_mock = Mock()
        add_rpm_mock.return_value = None

        add_maven_mock = Mock()
        add_maven_mock.return_value = None

        add_image_mock = Mock()
        add_image_mock.return_value = None

        # Queue responses for all build types
        self.queue_client_response('listBTypes', list_rpm_mock)
        self.queue_client_response('addBType', add_rpm_mock)

        self.queue_client_response('listBTypes', list_maven_mock)
        self.queue_client_response('addBType', add_maven_mock)

        self.queue_client_response('listBTypes', list_image_mock)
        self.queue_client_response('addBType', add_image_mock)

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
        list_rpm_mock.assert_called_once_with(query={'name': 'rpm'})
        list_maven_mock.assert_called_once_with(query={'name': 'maven'})
        list_image_mock.assert_called_once_with(query={'name': 'image'})
        add_rpm_mock.assert_called_once_with('rpm')
        add_maven_mock.assert_called_once_with('maven')
        add_image_mock.assert_called_once_with('image')

    def test_build_type_mixed_new_and_existing(self):
        """Test processing a mix of new and existing build types."""
        build_types = [
            create_test_build_type('rpm'),  # Already exists
            create_test_build_type('win'),  # New
        ]
        solver = create_solver_with_objects(build_types)
        mock_session = create_test_koji_session()

        # Mock rpm as existing
        list_rpm_mock = Mock()
        list_rpm_mock.return_value = [{'id': 1, 'name': 'rpm'}]

        # Mock win as not existing
        list_win_mock = Mock()
        list_win_mock.return_value = []

        add_win_mock = Mock()
        add_win_mock.return_value = None

        # Queue responses
        self.queue_client_response('listBTypes', list_rpm_mock)
        self.queue_client_response('listBTypes', list_win_mock)
        self.queue_client_response('addBType', add_win_mock)

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

        # Verify rpm was checked but not created
        list_rpm_mock.assert_called_once_with(query={'name': 'rpm'})

        # Verify win was created
        list_win_mock.assert_called_once_with(query={'name': 'win'})
        add_win_mock.assert_called_once_with('win')


# The end.

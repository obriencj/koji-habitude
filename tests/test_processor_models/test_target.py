"""
koji-habitude - test_processor.test_target

Unit tests for processor integration with target models and change reporting.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

from unittest import TestCase
from unittest.mock import Mock

from koji_habitude.models import Target
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


def create_test_target(name: str, build_tag: str, dest_tag: str = None) -> Target:
    """
    Create a test target with the specified parameters.

    Args:
        name: Target name
        build_tag: Build tag name
        dest_tag: Destination tag name (defaults to name if None)

    Returns:
        Target object for testing
    """
    return Target(
        name=name,
        **{'build-tag': build_tag, 'dest-tag': dest_tag},
        filename='test.yaml',
        lineno=1
    )


class TestProcessorTargetBehavior(MulticallMocking, TestCase):

    def test_target_creation(self):
        target = create_test_target('new-target', 'build-tag', 'dest-tag')
        solver = create_solver_with_objects([target])
        mock_session = create_test_koji_session()

        get_target_mock = Mock()
        get_target_mock.return_value = None

        create_mock = Mock()
        create_mock.return_value = None

        self.queue_client_response('getBuildTarget', get_target_mock)
        self.queue_client_response('createBuildTarget', create_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_target_mock.assert_called_once_with('new-target', strict=False)
        create_mock.assert_called_once_with('new-target', 'build-tag', 'dest-tag')


    def test_target_modification(self):
        target = create_test_target('existing-target', 'new-build-tag', 'new-dest-tag')
        solver = create_solver_with_objects([target])
        mock_session = create_test_koji_session()

        # Mock the getBuildTarget call to return existing target with different values
        get_target_mock = Mock()
        get_target_mock.return_value = {
            'build_tag_name': 'old-build-tag',
            'dest_tag_name': 'old-dest-tag'
        }

        # Mock the editBuildTarget call for the modification
        edit_mock = Mock()
        edit_mock.return_value = None

        self.queue_client_response('getBuildTarget', get_target_mock)
        self.queue_client_response('editBuildTarget', edit_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        # Verify the calls were made correctly
        get_target_mock.assert_called_once_with('existing-target', strict=False)
        edit_mock.assert_called_once_with('existing-target', 'existing-target', 'new-build-tag', 'new-dest-tag')


    def test_processor_summary(self):
        """
        Test that the processor summary is correct.
        """

        targets = [
            create_test_target('target1', 'build-tag1', 'dest-tag1'),
            create_test_target('target2', 'build-tag2', 'dest-tag2')
        ]
        solver = create_solver_with_objects(targets)
        mock_session = create_test_koji_session()

        # Mock getBuildTarget calls to return None (targets don't exist)
        get_target1_mock = Mock()
        get_target1_mock.return_value = None

        get_target2_mock = Mock()
        get_target2_mock.return_value = None

        # Mock createBuildTarget calls for target creation
        create1_mock = Mock()
        create1_mock.return_value = None

        create2_mock = Mock()
        create2_mock.return_value = None

        # Queue responses for both targets
        self.queue_client_response('getBuildTarget', get_target1_mock)
        self.queue_client_response('getBuildTarget', get_target2_mock)
        self.queue_client_response('createBuildTarget', create1_mock)
        self.queue_client_response('createBuildTarget', create2_mock)

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
        get_target1_mock.assert_called_once_with('target1', strict=False)
        get_target2_mock.assert_called_once_with('target2', strict=False)
        create1_mock.assert_called_once_with('target1', 'build-tag1', 'dest-tag1')
        create2_mock.assert_called_once_with('target2', 'build-tag2', 'dest-tag2')


# The end.
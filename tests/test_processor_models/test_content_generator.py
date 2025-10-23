"""
koji-habitude - test_processor_models.test_content_generator

Unit tests for processor integration with content generator models and change reporting.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 4.5 Sonnet via Cursor
"""

from unittest import TestCase
from unittest.mock import Mock

from koji_habitude.models import ContentGenerator
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


def create_test_content_generator(name: str, users: list = None,
                                  exact_users: bool = False) -> ContentGenerator:
    """
    Create a test content generator with the specified parameters.

    Args:
        name: Content generator name
        users: List of users with access (default empty list)
        exact_users: Whether to use exact user matching (default False)

    Returns:
        ContentGenerator object for testing
    """
    return ContentGenerator(
        name=name,
        users=users or [],
        exact_users=exact_users,
        filename='test.yaml',
        lineno=1
    )


class TestProcessorContentGeneratorBehavior(MulticallMocking, TestCase):

    def test_content_generator_creation(self):
        """Test creating a new content generator."""
        cg = create_test_content_generator('new-cg')
        solver = create_solver_with_objects([cg])
        mock_session = create_test_koji_session()

        # Mock the current user for CG creation
        mock_session._currentuser = {'id': 12345, 'name': 'testuser'}

        list_cgs_mock = Mock()
        list_cgs_mock.return_value = {}  # CG doesn't exist

        grant_mock = Mock()
        grant_mock.return_value = None

        revoke_mock = Mock()
        revoke_mock.return_value = None

        self.queue_client_response('listCGs', list_cgs_mock)
        self.queue_client_response('grantCGAccess', grant_mock)
        self.queue_client_response('revokeCGAccess', revoke_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        list_cgs_mock.assert_called_once_with()
        grant_mock.assert_called_once_with(12345, 'new-cg', create=True)
        revoke_mock.assert_called_once_with(12345, 'new-cg')

    def test_content_generator_creation_with_users(self):
        """Test creating a new content generator with users."""
        cg = create_test_content_generator('new-cg', users=['user1', 'user2'])
        solver = create_solver_with_objects([cg])
        mock_session = create_test_koji_session()

        # Mock the current user for CG creation
        mock_session._currentuser = {'id': 12345, 'name': 'testuser'}

        list_cgs_mock = Mock()
        list_cgs_mock.return_value = {}  # CG doesn't exist

        grant_create_mock = Mock()
        grant_create_mock.return_value = None

        revoke_mock = Mock()
        revoke_mock.return_value = None

        grant_user1_mock = Mock()
        grant_user1_mock.return_value = None

        grant_user2_mock = Mock()
        grant_user2_mock.return_value = None

        self.queue_client_response('listCGs', list_cgs_mock)
        self.queue_client_response('grantCGAccess', grant_create_mock)
        self.queue_client_response('revokeCGAccess', revoke_mock)
        self.queue_client_response('grantCGAccess', grant_user1_mock)
        self.queue_client_response('grantCGAccess', grant_user2_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        list_cgs_mock.assert_called_once_with()
        grant_create_mock.assert_called_once_with(12345, 'new-cg', create=True)
        revoke_mock.assert_called_once_with(12345, 'new-cg')
        grant_user1_mock.assert_called_once_with('user1', 'new-cg')
        grant_user2_mock.assert_called_once_with('user2', 'new-cg')

    def test_content_generator_add_missing_users(self):
        """Test adding users to an existing content generator."""
        cg = create_test_content_generator('existing-cg', users=['user1', 'user2'])
        solver = create_solver_with_objects([cg])
        mock_session = create_test_koji_session()

        # Mock listCGs to return existing CG with only user1
        list_cgs_mock = Mock()
        list_cgs_mock.return_value = {
            'existing-cg': {
                'id': 100,
                'users': ['user1']  # Only user1 exists
            }
        }

        grant_user2_mock = Mock()
        grant_user2_mock.return_value = None

        self.queue_client_response('listCGs', list_cgs_mock)
        self.queue_client_response('grantCGAccess', grant_user2_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        list_cgs_mock.assert_called_once_with()
        grant_user2_mock.assert_called_once_with('user2', 'existing-cg')

    def test_content_generator_remove_extra_users_with_exact(self):
        """Test removing users from a content generator when exact_users=True."""
        cg = create_test_content_generator('existing-cg', users=['user1'], exact_users=True)
        solver = create_solver_with_objects([cg])
        mock_session = create_test_koji_session()

        # Mock listCGs to return existing CG with extra user
        list_cgs_mock = Mock()
        list_cgs_mock.return_value = {
            'existing-cg': {
                'id': 100,
                'users': ['user1', 'extra-user']  # Has extra user
            }
        }

        revoke_mock = Mock()
        revoke_mock.return_value = None

        self.queue_client_response('listCGs', list_cgs_mock)
        self.queue_client_response('revokeCGAccess', revoke_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        list_cgs_mock.assert_called_once_with()
        revoke_mock.assert_called_once_with('extra-user', 'existing-cg')

    def test_content_generator_no_remove_without_exact(self):
        """Test not removing users when exact_users=False (default)."""
        cg = create_test_content_generator('existing-cg', users=['user1'], exact_users=False)
        solver = create_solver_with_objects([cg])
        mock_session = create_test_koji_session()

        # Mock listCGs to return existing CG with extra user
        list_cgs_mock = Mock()
        list_cgs_mock.return_value = {
            'existing-cg': {
                'id': 100,
                'users': ['user1', 'extra-user']  # Has extra user, but shouldn't be removed
            }
        }

        self.queue_client_response('listCGs', list_cgs_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        list_cgs_mock.assert_called_once_with()
        # Should not call revokeCGAccess

    def test_content_generator_no_changes_needed(self):
        """Test content generator that already matches desired state."""
        cg = create_test_content_generator('existing-cg', users=['user1', 'user2'])
        solver = create_solver_with_objects([cg])
        mock_session = create_test_koji_session()

        # Mock listCGs to return CG that already matches desired state
        list_cgs_mock = Mock()
        list_cgs_mock.return_value = {
            'existing-cg': {
                'id': 100,
                'users': ['user1', 'user2']  # Already matches
            }
        }

        self.queue_client_response('listCGs', list_cgs_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        list_cgs_mock.assert_called_once_with()

    def test_content_generator_add_and_remove_users(self):
        """Test both adding and removing users in the same change."""
        cg = create_test_content_generator('existing-cg',
                                          users=['user1', 'user3'],
                                          exact_users=True)
        solver = create_solver_with_objects([cg])
        mock_session = create_test_koji_session()

        # Mock listCGs to return CG with different users
        list_cgs_mock = Mock()
        list_cgs_mock.return_value = {
            'existing-cg': {
                'id': 100,
                'users': ['user1', 'user2']  # user2 should be removed, user3 should be added
            }
        }

        grant_user3_mock = Mock()
        grant_user3_mock.return_value = None

        revoke_user2_mock = Mock()
        revoke_user2_mock.return_value = None

        self.queue_client_response('listCGs', list_cgs_mock)
        self.queue_client_response('grantCGAccess', grant_user3_mock)
        self.queue_client_response('revokeCGAccess', revoke_user2_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        list_cgs_mock.assert_called_once_with()
        grant_user3_mock.assert_called_once_with('user3', 'existing-cg')
        revoke_user2_mock.assert_called_once_with('user2', 'existing-cg')

    def test_processor_summary_with_multiple_content_generators(self):
        """Test that the processor summary is correct with multiple content generators."""
        cgs = [
            create_test_content_generator('cg1', users=['user1']),
            create_test_content_generator('cg2', users=['user2', 'user3'])
        ]
        solver = create_solver_with_objects(cgs)
        mock_session = create_test_koji_session()

        # Mock the current user for CG creation
        mock_session._currentuser = {'id': 12345, 'name': 'testuser'}

        # Mock listCGs calls to return None (CGs don't exist)
        list_cgs1_mock = Mock()
        list_cgs1_mock.return_value = {}

        list_cgs2_mock = Mock()
        list_cgs2_mock.return_value = {}

        # Mock grantCGAccess calls for CG creation
        grant_create1_mock = Mock()
        grant_create1_mock.return_value = None

        grant_create2_mock = Mock()
        grant_create2_mock.return_value = None

        # Mock revokeCGAccess calls for CG creation
        revoke1_mock = Mock()
        revoke1_mock.return_value = None

        revoke2_mock = Mock()
        revoke2_mock.return_value = None

        # Mock grantCGAccess calls for users
        grant_user1_mock = Mock()
        grant_user1_mock.return_value = None

        grant_user2_mock = Mock()
        grant_user2_mock.return_value = None

        grant_user3_mock = Mock()
        grant_user3_mock.return_value = None

        # Queue responses for both CGs
        self.queue_client_response('listCGs', list_cgs1_mock)
        self.queue_client_response('grantCGAccess', grant_create1_mock)
        self.queue_client_response('revokeCGAccess', revoke1_mock)
        self.queue_client_response('grantCGAccess', grant_user1_mock)

        self.queue_client_response('listCGs', list_cgs2_mock)
        self.queue_client_response('grantCGAccess', grant_create2_mock)
        self.queue_client_response('revokeCGAccess', revoke2_mock)
        self.queue_client_response('grantCGAccess', grant_user2_mock)
        self.queue_client_response('grantCGAccess', grant_user3_mock)

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
        list_cgs1_mock.assert_called_once_with()
        list_cgs2_mock.assert_called_once_with()
        grant_create1_mock.assert_called_once_with(12345, 'cg1', create=True)
        grant_create2_mock.assert_called_once_with(12345, 'cg2', create=True)
        revoke1_mock.assert_called_once_with(12345, 'cg1')
        revoke2_mock.assert_called_once_with(12345, 'cg2')
        grant_user1_mock.assert_called_once_with('user1', 'cg1')
        grant_user2_mock.assert_called_once_with('user2', 'cg2')
        grant_user3_mock.assert_called_once_with('user3', 'cg2')


# The end.

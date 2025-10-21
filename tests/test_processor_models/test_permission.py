"""
koji-habitude - test_processor_models.test_permission

Unit tests for processor integration with permission models and change reporting.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

from unittest import TestCase
from unittest.mock import Mock

from koji_habitude.models import Permission
from koji_habitude.processor import (
    CompareOnlyProcessor,
    Processor,
    ProcessorState,
    ProcessorSummary,
)

from . import (
    MulticallMocking,
    create_empty_resolver,
    create_resolver_with_objects,
    create_solver_with_objects,
    create_test_koji_session,
)


def create_test_permission(name: str, description: str = None) -> Permission:
    """
    Create a test permission with the specified parameters.

    Args:
        name: Permission name
        description: Permission description (default None)

    Returns:
        Permission object for testing
    """
    return Permission(
        name=name,
        description=description,
        filename='test.yaml',
        lineno=1
    )


class TestProcessorPermissionBehavior(MulticallMocking, TestCase):

    def test_permission_creation(self):
        """Test creating a new permission with basic settings."""
        permission = create_test_permission('new-permission', 'Test permission description')
        solver = create_solver_with_objects([permission])
        mock_session = create_test_koji_session()

        get_permission_mock = Mock()
        get_permission_mock.return_value = []

        # Mock the current user for permission creation
        mock_session._currentuser = {'id': 12345}

        grant_mock = Mock()
        grant_mock.return_value = None

        revoke_mock = Mock()
        revoke_mock.return_value = None

        self.queue_client_response('getAllPerms', get_permission_mock)
        self.queue_client_response('grantPermission', grant_mock)
        self.queue_client_response('revokePermission', revoke_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_permission_mock.assert_called_once_with()
        grant_mock.assert_called_once_with(
            12345, 'new-permission', create=True,
            description='Test permission description')
        revoke_mock.assert_called_once_with(12345, 'new-permission')

    def test_permission_creation_without_description(self):
        """Test creating a new permission without description."""
        permission = create_test_permission('new-permission')
        solver = create_solver_with_objects([permission])
        mock_session = create_test_koji_session()

        get_permission_mock = Mock()
        get_permission_mock.return_value = []

        # Mock the current user for permission creation
        mock_session._currentuser = {'id': 12345}

        grant_mock = Mock()
        grant_mock.return_value = None

        revoke_mock = Mock()
        revoke_mock.return_value = None

        self.queue_client_response('getAllPerms', get_permission_mock)
        self.queue_client_response('grantPermission', grant_mock)
        self.queue_client_response('revokePermission', revoke_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_permission_mock.assert_called_once_with()
        grant_mock.assert_called_once_with(
            12345, 'new-permission', create=True, description=None)
        revoke_mock.assert_called_once_with(12345, 'new-permission')

    def test_permission_update_description(self):
        """Test updating an existing permission's description."""
        permission = create_test_permission('existing-permission', 'New description')
        solver = create_solver_with_objects([permission])
        mock_session = create_test_koji_session()

        # Mock the getPermission call to return existing permission with different description
        get_permission_mock = Mock()
        get_permission_mock.return_value = [{
            'id': 100,
            'name': 'existing-permission',
            'description': 'Old description'
        }]

        edit_mock = Mock()
        edit_mock.return_value = None

        self.queue_client_response('getAllPerms', get_permission_mock)
        self.queue_client_response('editPermission', edit_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_permission_mock.assert_called_once_with()
        edit_mock.assert_called_once_with('existing-permission', description='New description')

    def test_permission_no_changes_needed(self):
        """Test permission that already matches desired state."""
        permission = create_test_permission('existing-permission', 'Same description')
        solver = create_solver_with_objects([permission])
        mock_session = create_test_koji_session()

        # Mock the getPermission call to return permission that already matches desired state
        get_permission_mock = Mock()
        get_permission_mock.return_value = [{
            'id': 100,
            'name': 'existing-permission',
            'description': 'Same description'  # Already matches
        }]

        self.queue_client_response('getAllPerms', get_permission_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_permission_mock.assert_called_once_with()

    def test_permission_update_description_from_none(self):
        """Test updating a permission that has no description to have one."""
        permission = create_test_permission('existing-permission', 'New description')
        solver = create_solver_with_objects([permission])
        mock_session = create_test_koji_session()

        # Mock the getPermission call to return permission with no description
        get_permission_mock = Mock()
        get_permission_mock.return_value = [{
            'id': 100,
            'name': 'existing-permission',
            'description': None  # No current description
        }]

        edit_mock = Mock()
        edit_mock.return_value = None

        self.queue_client_response('getAllPerms', get_permission_mock)
        self.queue_client_response('editPermission', edit_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_permission_mock.assert_called_once_with()
        edit_mock.assert_called_once_with('existing-permission', description='New description')

    def test_permission_remove_description(self):
        """Test updating a permission to remove its description."""
        permission = create_test_permission('existing-permission')  # No description desired
        solver = create_solver_with_objects([permission])
        mock_session = create_test_koji_session()

        # Mock the getPermission call to return permission with a description
        get_permission_mock = Mock()
        get_permission_mock.return_value = [{
            'id': 100,
            'name': 'existing-permission',
            'description': 'Old description'  # Has current description
        }]

        edit_mock = Mock()
        edit_mock.return_value = None

        self.queue_client_response('getAllPerms', get_permission_mock)
        self.queue_client_response('editPermission', edit_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_permission_mock.assert_called_once_with()
        edit_mock.assert_called_once_with('existing-permission', description=None)

    def test_processor_summary_with_multiple_permissions(self):
        """Test that the processor summary is correct with multiple permissions."""
        permissions = [
            create_test_permission('perm1', 'First permission'),
            create_test_permission('perm2', 'Second permission')
        ]
        solver = create_solver_with_objects(permissions)
        mock_session = create_test_koji_session()

        # Mock getPermission calls to return None (permissions don't exist)
        get_perm1_mock = Mock()
        get_perm1_mock.return_value = []

        get_perm2_mock = Mock()
        get_perm2_mock.return_value = []

        # Mock the current user for permission creation
        mock_session._currentuser = {'id': 12345}

        # Mock grantPermission calls for permission creation
        grant1_mock = Mock()
        grant1_mock.return_value = None

        grant2_mock = Mock()
        grant2_mock.return_value = None

        # Mock revokePermission calls for permission creation
        revoke1_mock = Mock()
        revoke1_mock.return_value = None

        revoke2_mock = Mock()
        revoke2_mock.return_value = None

        # Queue responses for both permissions
        self.queue_client_response('getAllPerms', get_perm1_mock)
        self.queue_client_response('grantPermission', grant1_mock)
        self.queue_client_response('revokePermission', revoke1_mock)

        self.queue_client_response('getAllPerms', get_perm2_mock)
        self.queue_client_response('grantPermission', grant2_mock)
        self.queue_client_response('revokePermission', revoke2_mock)

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
        get_perm1_mock.assert_called_once_with()
        get_perm2_mock.assert_called_once_with()
        grant1_mock.assert_called_once_with(
            12345, 'perm1', create=True, description='First permission')
        grant2_mock.assert_called_once_with(
            12345, 'perm2', create=True, description='Second permission')
        revoke1_mock.assert_called_once_with(12345, 'perm1')
        revoke2_mock.assert_called_once_with(12345, 'perm2')


# The end.

"""
koji-habitude - test_processor_models.test_user

Unit tests for processor integration with user models and change reporting.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

from unittest import TestCase
from unittest.mock import Mock

from koji_habitude.processor import Processor, DiffOnlyProcessor, ProcessorState, ProcessorSummary
from koji_habitude.models import User

from . import create_test_koji_session, create_solver_with_objects, MulticallMocking


def create_test_user(name: str, enabled: bool = True, groups: list = None, permissions: list = None,
                    exact_groups: bool = False, exact_permissions: bool = False) -> User:
    """
    Create a test user with the specified parameters.

    Args:
        name: User name
        enabled: Whether user is enabled (default True)
        groups: List of group names (default empty list)
        permissions: List of permission names (default empty list)
        exact_groups: Whether to use exact group matching (default False)
        exact_permissions: Whether to use exact permission matching (default False)

    Returns:
        User object for testing
    """

    return User(
        name=name,
        enabled=enabled,
        groups=groups or [],
        permissions=permissions or [],
        exact_groups=exact_groups,
        exact_permissions=exact_permissions,
        filename='test.yaml',
        lineno=1
    )


class TestProcessorUserBehavior(MulticallMocking, TestCase):

    def test_user_creation(self):
        """Test creating a new user with basic settings."""
        user = create_test_user('new-user', enabled=True)
        solver = create_solver_with_objects([user])
        mock_session = create_test_koji_session()

        get_user_mock = Mock()
        get_user_mock.return_value = None

        get_perms_mock = Mock()
        get_perms_mock.return_value = []

        create_mock = Mock()
        create_mock.return_value = None

        self.queue_client_response('getUser', get_user_mock)
        self.queue_client_response('getUserPerms', get_perms_mock)
        self.queue_client_response('createUser', create_mock)

        processor = Processor(
            koji_session=mock_session,
            stream_origin=solver,
            resolver=None,
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_user_mock.assert_called_once_with('new-user', strict=False, groups=True)
        get_perms_mock.assert_called_once_with('new-user')
        create_mock.assert_called_once_with('new-user', status=0)

    def test_user_creation_with_groups_and_permissions(self):
        """Test creating a user with groups and permissions."""
        user = create_test_user('new-user', enabled=True, groups=['group1', 'group2'],
                               permissions=['perm1', 'perm2'])
        solver = create_solver_with_objects([user])
        mock_session = create_test_koji_session()

        get_user_mock = Mock()
        get_user_mock.return_value = None

        get_perms_mock = Mock()
        get_perms_mock.return_value = []

        create_mock = Mock()
        create_mock.return_value = None

        grant_perm1_mock = Mock()
        grant_perm1_mock.return_value = None

        grant_perm2_mock = Mock()
        grant_perm2_mock.return_value = None

        add_group1_mock = Mock()
        add_group1_mock.return_value = None

        add_group2_mock = Mock()
        add_group2_mock.return_value = None

        self.queue_client_response('getUser', get_user_mock)
        self.queue_client_response('getUserPerms', get_perms_mock)
        self.queue_client_response('createUser', create_mock)
        self.queue_client_response('grantPermission', grant_perm1_mock)
        self.queue_client_response('grantPermission', grant_perm2_mock)
        self.queue_client_response('addGroupMember', add_group1_mock)
        self.queue_client_response('addGroupMember', add_group2_mock)

        processor = Processor(
            koji_session=mock_session,
            stream_origin=solver,
            resolver=None,
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        # Verify all calls were made
        get_user_mock.assert_called_once_with('new-user', strict=False, groups=True)
        get_perms_mock.assert_called_once_with('new-user')
        create_mock.assert_called_once_with('new-user', status=0)
        grant_perm1_mock.assert_called_once_with('new-user', 'perm1', create=True)
        grant_perm2_mock.assert_called_once_with('new-user', 'perm2', create=True)
        add_group1_mock.assert_called_once_with('group1', 'new-user', strict=False)
        add_group2_mock.assert_called_once_with('group2', 'new-user', strict=False)

    def test_user_enable_existing_disabled_user(self):
        """Test enabling an existing disabled user."""
        user = create_test_user('existing-user', enabled=True)
        solver = create_solver_with_objects([user])
        mock_session = create_test_koji_session()

        # Mock the getUser call to return existing user with disabled status
        get_user_mock = Mock()
        get_user_mock.return_value = {
            'name': 'existing-user',
            'status': 1,  # User is disabled
            'groups': []
        }

        get_perms_mock = Mock()
        get_perms_mock.return_value = []

        enable_mock = Mock()
        enable_mock.return_value = None

        self.queue_client_response('getUser', get_user_mock)
        self.queue_client_response('getUserPerms', get_perms_mock)
        self.queue_client_response('enableUser', enable_mock)

        processor = Processor(
            koji_session=mock_session,
            stream_origin=solver,
            resolver=None,
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_user_mock.assert_called_once_with('existing-user', strict=False, groups=True)
        get_perms_mock.assert_called_once_with('existing-user')
        enable_mock.assert_called_once_with('existing-user')

    def test_user_disable_existing_enabled_user(self):
        """Test disabling an existing enabled user."""
        user = create_test_user('existing-user', enabled=False)
        solver = create_solver_with_objects([user])
        mock_session = create_test_koji_session()

        # Mock the getUser call to return existing user with enabled status
        get_user_mock = Mock()
        get_user_mock.return_value = {
            'name': 'existing-user',
            'status': 0,  # User is enabled
            'groups': []
        }

        get_perms_mock = Mock()
        get_perms_mock.return_value = []

        disable_mock = Mock()
        disable_mock.return_value = None

        self.queue_client_response('getUser', get_user_mock)
        self.queue_client_response('getUserPerms', get_perms_mock)
        self.queue_client_response('disableUser', disable_mock)

        processor = Processor(
            koji_session=mock_session,
            stream_origin=solver,
            resolver=None,
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_user_mock.assert_called_once_with('existing-user', strict=False, groups=True)
        get_perms_mock.assert_called_once_with('existing-user')
        disable_mock.assert_called_once_with('existing-user')

    def test_user_add_missing_groups(self):
        """Test adding user to groups they're not currently in."""
        user = create_test_user('existing-user', groups=['group1', 'group2'])
        solver = create_solver_with_objects([user])
        mock_session = create_test_koji_session()

        # Mock the getUser call to return user with no groups
        get_user_mock = Mock()
        get_user_mock.return_value = {
            'name': 'existing-user',
            'status': 0,  # User is enabled
            'groups': []  # User has no groups currently
        }

        get_perms_mock = Mock()
        get_perms_mock.return_value = []

        add_group1_mock = Mock()
        add_group1_mock.return_value = None

        add_group2_mock = Mock()
        add_group2_mock.return_value = None

        self.queue_client_response('getUser', get_user_mock)
        self.queue_client_response('getUserPerms', get_perms_mock)
        self.queue_client_response('addGroupMember', add_group1_mock)
        self.queue_client_response('addGroupMember', add_group2_mock)

        processor = Processor(
            koji_session=mock_session,
            stream_origin=solver,
            resolver=None,
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_user_mock.assert_called_once_with('existing-user', strict=False, groups=True)
        get_perms_mock.assert_called_once_with('existing-user')
        add_group1_mock.assert_called_once_with('group1', 'existing-user', strict=False)
        add_group2_mock.assert_called_once_with('group2', 'existing-user', strict=False)

    def test_user_remove_extra_groups_with_exact_groups(self):
        """Test removing user from groups when exact_groups=True."""
        user = create_test_user('existing-user', groups=['group1'], exact_groups=True)
        solver = create_solver_with_objects([user])
        mock_session = create_test_koji_session()

        # Mock the getUser call to return user with extra groups
        get_user_mock = Mock()
        get_user_mock.return_value = {
            'name': 'existing-user',
            'status': 0,  # User is enabled
            'groups': ['group1', 'extra-group']  # User has extra group
        }

        get_perms_mock = Mock()
        get_perms_mock.return_value = []

        remove_group_mock = Mock()
        remove_group_mock.return_value = None

        self.queue_client_response('getUser', get_user_mock)
        self.queue_client_response('getUserPerms', get_perms_mock)
        self.queue_client_response('dropGroupMember', remove_group_mock)

        processor = Processor(
            koji_session=mock_session,
            stream_origin=solver,
            resolver=None,
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_user_mock.assert_called_once_with('existing-user', strict=False, groups=True)
        get_perms_mock.assert_called_once_with('existing-user')
        remove_group_mock.assert_called_once_with('extra-group', 'existing-user')

    def test_user_grant_missing_permissions(self):
        """Test granting permissions the user doesn't currently have."""
        user = create_test_user('existing-user', permissions=['perm1', 'perm2'])
        solver = create_solver_with_objects([user])
        mock_session = create_test_koji_session()

        # Mock the getUser call to return user with no permissions
        get_user_mock = Mock()
        get_user_mock.return_value = {
            'name': 'existing-user',
            'status': 0,  # User is enabled
            'groups': []
        }

        get_perms_mock = Mock()
        get_perms_mock.return_value = []  # User has no permissions currently

        grant_perm1_mock = Mock()
        grant_perm1_mock.return_value = None

        grant_perm2_mock = Mock()
        grant_perm2_mock.return_value = None

        self.queue_client_response('getUser', get_user_mock)
        self.queue_client_response('getUserPerms', get_perms_mock)
        self.queue_client_response('grantPermission', grant_perm1_mock)
        self.queue_client_response('grantPermission', grant_perm2_mock)

        processor = Processor(
            koji_session=mock_session,
            stream_origin=solver,
            resolver=None,
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_user_mock.assert_called_once_with('existing-user', strict=False, groups=True)
        get_perms_mock.assert_called_once_with('existing-user')
        grant_perm1_mock.assert_called_once_with('existing-user', 'perm1', create=True)
        grant_perm2_mock.assert_called_once_with('existing-user', 'perm2', create=True)

    def test_user_revoke_extra_permissions_with_exact_permissions(self):
        """Test revoking permissions when exact_permissions=True."""
        user = create_test_user('existing-user', permissions=['perm1'], exact_permissions=True)
        solver = create_solver_with_objects([user])
        mock_session = create_test_koji_session()

        # Mock the getUser call to return user with extra permissions
        get_user_mock = Mock()
        get_user_mock.return_value = {
            'name': 'existing-user',
            'status': 0,  # User is enabled
            'groups': []
        }

        get_perms_mock = Mock()
        get_perms_mock.return_value = ['perm1', 'extra-perm']  # User has extra permission

        revoke_perm_mock = Mock()
        revoke_perm_mock.return_value = None

        self.queue_client_response('getUser', get_user_mock)
        self.queue_client_response('getUserPerms', get_perms_mock)
        self.queue_client_response('revokePermission', revoke_perm_mock)

        processor = Processor(
            koji_session=mock_session,
            stream_origin=solver,
            resolver=None,
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_user_mock.assert_called_once_with('existing-user', strict=False, groups=True)
        get_perms_mock.assert_called_once_with('existing-user')
        revoke_perm_mock.assert_called_once_with('existing-user', 'extra-perm')

    def test_user_no_changes_needed(self):
        """Test user that already matches desired state."""
        user = create_test_user('existing-user', enabled=True, groups=['group1'], permissions=['perm1'])
        solver = create_solver_with_objects([user])
        mock_session = create_test_koji_session()

        # Mock the getUser call to return user that already matches desired state
        get_user_mock = Mock()
        get_user_mock.return_value = {
            'name': 'existing-user',
            'status': 0,  # Already enabled
            'groups': ['group1']  # Already in group1
        }

        get_perms_mock = Mock()
        get_perms_mock.return_value = ['perm1']  # Already has perm1

        self.queue_client_response('getUser', get_user_mock)
        self.queue_client_response('getUserPerms', get_perms_mock)

        processor = Processor(
            koji_session=mock_session,
            stream_origin=solver,
            resolver=None,
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_user_mock.assert_called_once_with('existing-user', strict=False, groups=True)
        get_perms_mock.assert_called_once_with('existing-user')

    def test_processor_summary_with_multiple_users(self):
        """Test that the processor summary is correct with multiple users."""
        users = [
            create_test_user('user1', enabled=True, groups=['group1']),
            create_test_user('user2', enabled=False, permissions=['perm1'])
        ]
        solver = create_solver_with_objects(users)
        mock_session = create_test_koji_session()

        # Mock getUser calls to return None (users don't exist)
        get_user1_mock = Mock()
        get_user1_mock.return_value = None

        get_user2_mock = Mock()
        get_user2_mock.return_value = None

        # Mock getUserPerms calls
        get_perms1_mock = Mock()
        get_perms1_mock.return_value = []

        get_perms2_mock = Mock()
        get_perms2_mock.return_value = []

        # Mock createUser calls for user creation
        create1_mock = Mock()
        create1_mock.return_value = None

        create2_mock = Mock()
        create2_mock.return_value = None

        # Mock addGroupMember call for user1
        add_group1_mock = Mock()
        add_group1_mock.return_value = None

        # Mock grantPermission call for user2
        grant_perm1_mock = Mock()
        grant_perm1_mock.return_value = None

        # Queue responses for both users
        self.queue_client_response('getUser', get_user1_mock)
        self.queue_client_response('getUserPerms', get_perms1_mock)
        self.queue_client_response('createUser', create1_mock)
        self.queue_client_response('addGroupMember', add_group1_mock)

        self.queue_client_response('getUser', get_user2_mock)
        self.queue_client_response('getUserPerms', get_perms2_mock)
        self.queue_client_response('createUser', create2_mock)
        self.queue_client_response('grantPermission', grant_perm1_mock)

        processor = Processor(
            koji_session=mock_session,
            stream_origin=solver,
            resolver=None,
            chunk_size=10
        )

        summary = processor.run()
        self.assertIsInstance(summary, ProcessorSummary)
        self.assertEqual(summary.total_objects, 2)
        self.assertEqual(summary.steps_completed, 1)
        self.assertEqual(summary.state, ProcessorState.EXHAUSTED)

        # Verify all calls were made
        get_user1_mock.assert_called_once_with('user1', strict=False, groups=True)
        get_user2_mock.assert_called_once_with('user2', strict=False, groups=True)
        get_perms1_mock.assert_called_once_with('user1')
        get_perms2_mock.assert_called_once_with('user2')
        create1_mock.assert_called_once_with('user1', status=0)
        create2_mock.assert_called_once_with('user2', status=1)
        add_group1_mock.assert_called_once_with('group1', 'user1', strict=False)
        grant_perm1_mock.assert_called_once_with('user2', 'perm1', create=True)


# The end.

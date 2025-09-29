"""
koji-habitude - test_processor_models.test_group

Unit tests for processor integration with group models and change reporting.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

from unittest import TestCase
from unittest.mock import Mock

from koji_habitude.processor import Processor, DiffOnlyProcessor, ProcessorState, ProcessorSummary
from koji_habitude.models import Group

from . import create_test_koji_session, create_solver_with_objects, MulticallMocking


def create_test_group(name: str, members: list = None, permissions: list = None) -> Group:
    """
    Create a test group with the specified parameters.

    Args:
        name: Group name
        members: List of member names (default empty list)
        permissions: List of permission names (default empty list)

    Returns:
        Group object for testing
    """
    return Group(
        name=name,
        members=members or [],
        permissions=permissions or [],
        filename='test.yaml',
        lineno=1
    )


class TestProcessorGroupBehavior(MulticallMocking, TestCase):

    def test_group_creation(self):
        """Test creating a new group with basic settings."""
        group = create_test_group('new-group')
        solver = create_solver_with_objects([group])
        mock_session = create_test_koji_session()

        get_group_mock = Mock()
        get_group_mock.return_value = None

        get_members_mock = Mock()
        get_members_mock.return_value = []

        get_perms_mock = Mock()
        get_perms_mock.return_value = []

        create_mock = Mock()
        create_mock.return_value = None

        self.queue_client_response('getUser', get_group_mock)
        self.queue_client_response('getGroupMembers', get_members_mock)
        self.queue_client_response('getUserPerms', get_perms_mock)
        self.queue_client_response('newGroup', create_mock)

        processor = Processor(
            koji_session=mock_session,
            stream_origin=solver,
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_group_mock.assert_called_once_with('new-group', strict=False)
        get_members_mock.assert_not_called()
        get_perms_mock.assert_not_called()
        create_mock.assert_called_once_with('new-group')

    def test_group_creation_with_members_and_permissions(self):
        """Test creating a group with members and permissions."""
        group = create_test_group('new-group', members=['user1', 'user2'],
                                 permissions=['perm1', 'perm2'])
        solver = create_solver_with_objects([group])
        mock_session = create_test_koji_session()

        get_group_mock = Mock()
        get_group_mock.return_value = None

        get_members_mock = Mock()
        get_members_mock.return_value = []

        get_perms_mock = Mock()
        get_perms_mock.return_value = []

        create_mock = Mock()
        create_mock.return_value = None

        add_member1_mock = Mock()
        add_member1_mock.return_value = None

        add_member2_mock = Mock()
        add_member2_mock.return_value = None

        add_perm1_mock = Mock()
        add_perm1_mock.return_value = None

        add_perm2_mock = Mock()
        add_perm2_mock.return_value = None

        self.queue_client_response('getUser', get_group_mock)
        self.queue_client_response('getGroupMembers', get_members_mock)
        self.queue_client_response('getUserPerms', get_perms_mock)
        self.queue_client_response('newGroup', create_mock)
        self.queue_client_response('addGroupMember', add_member1_mock)
        self.queue_client_response('addGroupMember', add_member2_mock)
        self.queue_client_response('grantPermission', add_perm1_mock)
        self.queue_client_response('grantPermission', add_perm2_mock)

        processor = Processor(
            koji_session=mock_session,
            stream_origin=solver,
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        # Verify all calls were made
        get_group_mock.assert_called_once_with('new-group', strict=False)
        get_members_mock.assert_not_called()
        get_perms_mock.assert_not_called()
        create_mock.assert_called_once_with('new-group')
        add_member1_mock.assert_called_once_with('new-group', 'user1')
        add_member2_mock.assert_called_once_with('new-group', 'user2')
        add_perm1_mock.assert_called_once_with('new-group', 'perm1', create=True)
        add_perm2_mock.assert_called_once_with('new-group', 'perm2', create=True)

    def test_group_add_missing_members(self):
        """Test adding members to a group that doesn't have them."""
        group = create_test_group('existing-group', members=['user1', 'user2'])
        solver = create_solver_with_objects([group])
        mock_session = create_test_koji_session()

        # Mock the getUser call to return existing group with no members
        get_group_mock = Mock()
        get_group_mock.return_value = {
            'name': 'existing-group',
            'status': 0,  # Group is enabled
            'permissions': []
        }

        get_members_mock = Mock()
        get_members_mock.return_value = []  # Group has no members currently

        get_perms_mock = Mock()
        get_perms_mock.return_value = []

        add_member1_mock = Mock()
        add_member1_mock.return_value = None

        add_member2_mock = Mock()
        add_member2_mock.return_value = None

        self.queue_client_response('getUser', get_group_mock)
        self.queue_client_response('getGroupMembers', get_members_mock)
        self.queue_client_response('getUserPerms', get_perms_mock)
        self.queue_client_response('addGroupMember', add_member1_mock)
        self.queue_client_response('addGroupMember', add_member2_mock)

        processor = Processor(
            koji_session=mock_session,
            stream_origin=solver,
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_group_mock.assert_called_once_with('existing-group', strict=False)
        get_members_mock.assert_called_once_with('existing-group')
        get_perms_mock.assert_called_once_with('existing-group')
        add_member1_mock.assert_called_once_with('existing-group', 'user1')
        add_member2_mock.assert_called_once_with('existing-group', 'user2')

    def test_group_remove_extra_members(self):
        """Test removing members from a group when they shouldn't be there."""
        group = create_test_group('existing-group', members=['user1'])
        solver = create_solver_with_objects([group])
        mock_session = create_test_koji_session()

        # Mock the getUser call to return existing group with extra members
        get_group_mock = Mock()
        get_group_mock.return_value = {
            'name': 'existing-group',
            'status': 0,  # Group is enabled
            'permissions': []
        }

        get_members_mock = Mock()
        get_members_mock.return_value = [
            {"name": 'user1'},
            {"name": 'extra-user'}
        ]  # Group has extra member

        get_perms_mock = Mock()
        get_perms_mock.return_value = []

        remove_member_mock = Mock()
        remove_member_mock.return_value = None

        self.queue_client_response('getUser', get_group_mock)
        self.queue_client_response('getGroupMembers', get_members_mock)
        self.queue_client_response('getUserPerms', get_perms_mock)
        self.queue_client_response('dropGroupMember', remove_member_mock)

        processor = Processor(
            koji_session=mock_session,
            stream_origin=solver,
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_group_mock.assert_called_once_with('existing-group', strict=False)
        get_members_mock.assert_called_once_with('existing-group')
        get_perms_mock.assert_called_once_with('existing-group')
        remove_member_mock.assert_called_once_with('existing-group', 'extra-user')

    def test_group_add_missing_permissions(self):
        """Test adding permissions to a group that doesn't have them."""
        group = create_test_group('existing-group', permissions=['perm1', 'perm2'])
        solver = create_solver_with_objects([group])
        mock_session = create_test_koji_session()

        # Mock the getUser call to return existing group with no permissions
        get_group_mock = Mock()
        get_group_mock.return_value = {
            'name': 'existing-group',
            'status': 0,  # Group is enabled
            'permissions': []
        }

        get_members_mock = Mock()
        get_members_mock.return_value = []

        get_perms_mock = Mock()
        get_perms_mock.return_value = []  # Group has no permissions currently

        add_perm1_mock = Mock()
        add_perm1_mock.return_value = None

        add_perm2_mock = Mock()
        add_perm2_mock.return_value = None

        self.queue_client_response('getUser', get_group_mock)
        self.queue_client_response('getGroupMembers', get_members_mock)
        self.queue_client_response('getUserPerms', get_perms_mock)
        self.queue_client_response('grantPermission', add_perm1_mock)
        self.queue_client_response('grantPermission', add_perm2_mock)

        processor = Processor(
            koji_session=mock_session,
            stream_origin=solver,
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_group_mock.assert_called_once_with('existing-group', strict=False)
        get_members_mock.assert_called_once_with('existing-group')
        get_perms_mock.assert_called_once_with('existing-group')
        add_perm1_mock.assert_called_once_with('existing-group', 'perm1', create=True)
        add_perm2_mock.assert_called_once_with('existing-group', 'perm2', create=True)

    def test_group_remove_extra_permissions(self):
        """Test removing permissions from a group when they shouldn't be there."""
        group = create_test_group('existing-group', permissions=['perm1'])
        solver = create_solver_with_objects([group])
        mock_session = create_test_koji_session()

        # Mock the getUser call to return existing group with extra permissions
        get_group_mock = Mock()
        get_group_mock.return_value = {
            'name': 'existing-group',
            'status': 0,  # Group is enabled
            'permissions': []
        }

        get_members_mock = Mock()
        get_members_mock.return_value = []

        get_perms_mock = Mock()
        get_perms_mock.return_value = ['perm1', 'extra-perm']  # Group has extra permission

        remove_perm_mock = Mock()
        remove_perm_mock.return_value = None

        self.queue_client_response('getUser', get_group_mock)
        self.queue_client_response('getGroupMembers', get_members_mock)
        self.queue_client_response('getUserPerms', get_perms_mock)
        self.queue_client_response('revokePermission', remove_perm_mock)

        processor = Processor(
            koji_session=mock_session,
            stream_origin=solver,
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_group_mock.assert_called_once_with('existing-group', strict=False)
        get_members_mock.assert_called_once_with('existing-group')
        get_perms_mock.assert_called_once_with('existing-group')
        remove_perm_mock.assert_called_once_with('existing-group', 'extra-perm')

    def test_group_no_changes_needed(self):
        """Test group that already matches desired state."""
        group = create_test_group('existing-group', members=['user1'], permissions=['perm1'])
        solver = create_solver_with_objects([group])
        mock_session = create_test_koji_session()

        # Mock the getUser call to return group that already matches desired state
        get_group_mock = Mock()
        get_group_mock.return_value = {
            'name': 'existing-group',
            'status': 0,  # Group is enabled
            'permissions': ['perm1']  # Already has perm1
        }

        get_members_mock = Mock()
        get_members_mock.return_value = [{"name": 'user1'}]  # Already has user1

        get_perms_mock = Mock()
        get_perms_mock.return_value = ['perm1']  # Already has perm1

        self.queue_client_response('getUser', get_group_mock)
        self.queue_client_response('getGroupMembers', get_members_mock)
        self.queue_client_response('getUserPerms', get_perms_mock)

        processor = Processor(
            koji_session=mock_session,
            stream_origin=solver,
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_group_mock.assert_called_once_with('existing-group', strict=False)
        get_members_mock.assert_called_once_with('existing-group')
        get_perms_mock.assert_called_once_with('existing-group')

    def test_processor_summary_with_multiple_groups(self):
        """Test that the processor summary is correct with multiple groups."""
        groups = [
            create_test_group('group1', members=['user1']),
            create_test_group('group2', permissions=['perm1'])
        ]
        solver = create_solver_with_objects(groups)
        mock_session = create_test_koji_session()

        # Mock getUser calls to return None (groups don't exist)
        get_group1_mock = Mock()
        get_group1_mock.return_value = None

        get_group2_mock = Mock()
        get_group2_mock.return_value = None

        # Mock getGroupMembers calls
        get_members1_mock = Mock()
        get_members1_mock.return_value = []

        get_members2_mock = Mock()
        get_members2_mock.return_value = []

        # Mock getUserPerms calls
        get_perms1_mock = Mock()
        get_perms1_mock.return_value = []

        get_perms2_mock = Mock()
        get_perms2_mock.return_value = []

        # Mock newGroup calls for group creation
        create1_mock = Mock()
        create1_mock.return_value = None

        create2_mock = Mock()
        create2_mock.return_value = None

        # Mock addGroupMember call for group1
        add_member1_mock = Mock()
        add_member1_mock.return_value = None

        # Mock grantPermission call for group2
        add_perm1_mock = Mock()
        add_perm1_mock.return_value = None

        # Queue responses for both groups
        self.queue_client_response('getUser', get_group1_mock)
        self.queue_client_response('getGroupMembers', get_members1_mock)
        self.queue_client_response('getUserPerms', get_perms1_mock)
        self.queue_client_response('newGroup', create1_mock)
        self.queue_client_response('addGroupMember', add_member1_mock)

        self.queue_client_response('getUser', get_group2_mock)
        self.queue_client_response('getGroupMembers', get_members2_mock)
        self.queue_client_response('getUserPerms', get_perms2_mock)
        self.queue_client_response('newGroup', create2_mock)
        self.queue_client_response('grantPermission', add_perm1_mock)

        processor = Processor(
            koji_session=mock_session,
            stream_origin=solver,
            chunk_size=10
        )

        summary = processor.run()
        self.assertIsInstance(summary, ProcessorSummary)
        self.assertEqual(summary.total_objects, 2)
        self.assertEqual(summary.steps_completed, 1)
        self.assertEqual(summary.state, ProcessorState.EXHAUSTED)

        # Verify all calls were made
        get_group1_mock.assert_called_once_with('group1', strict=False)
        get_group2_mock.assert_called_once_with('group2', strict=False)
        get_members1_mock.assert_not_called()
        get_members2_mock.assert_not_called()
        get_perms1_mock.assert_not_called()
        get_perms2_mock.assert_not_called()
        create1_mock.assert_called_once_with('group1')
        create2_mock.assert_called_once_with('group2')
        add_member1_mock.assert_called_once_with('group1', 'user1')
        add_perm1_mock.assert_called_once_with('group2', 'perm1', create=True)


# The end.

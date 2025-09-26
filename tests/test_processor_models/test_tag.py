"""
koji-habitude - test_processor_models.test_tag

Unit tests for processor integration with tag models and change reporting.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

from unittest import TestCase
from unittest.mock import Mock

from koji_habitude.processor import Processor, DiffOnlyProcessor, ProcessorState, ProcessorSummary
from koji_habitude.models import Tag
from koji_habitude.models.tag import InheritanceLink

from . import create_test_koji_session, create_solver_with_objects, MulticallMocking


def create_test_tag(name: str, locked: bool = False, permission: str = None,
                   arches: list = None, maven_support: bool = False,
                   maven_include_all: bool = False, extras: dict = None,
                   groups: dict = None, inheritance: list = None,
                   external_repos: list = None) -> Tag:
    """
    Create a test tag with the specified parameters.

    Args:
        name: Tag name
        locked: Whether tag is locked (default False)
        permission: Permission name (default None)
        arches: List of architectures (default empty list)
        maven_support: Whether maven support is enabled (default False)
        maven_include_all: Whether maven include all is enabled (default False)
        extras: Extra tag data (default empty dict)
        groups: Tag groups dict (default empty dict)
        inheritance: List of inheritance links (default empty list)
        external_repos: List of external repo links (default empty list)

    Returns:
        Tag object for testing
    """
    return Tag(
        name=name,
        locked=locked,
        permission=permission,
        arches=arches or [],
        maven_support=maven_support,
        maven_include_all=maven_include_all,
        extras=extras or {},
        groups=groups or {},
        inheritance=inheritance or [],
        external_repos=external_repos or [],
        filename='test.yaml',
        lineno=1
    )


def create_inheritance_link(name: str, priority: int = None) -> InheritanceLink:
    """Create an inheritance link for testing."""
    return InheritanceLink(name=name, priority=priority)


class TestProcessorTagBehavior(MulticallMocking, TestCase):

    def test_tag_creation(self):
        """Test creating a new tag with basic settings."""
        tag = create_test_tag('new-tag', locked=False, arches=['x86_64'])
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        get_tag_mock = Mock()
        get_tag_mock.return_value = None

        get_groups_mock = Mock()
        get_groups_mock.return_value = []

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        create_mock = Mock()
        create_mock.return_value = None

        set_extras_mock = Mock()
        set_extras_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('createTag', create_mock)
        self.queue_client_response('editTag2', set_extras_mock)

        processor = Processor(
            koji_session=mock_session,
            stream_origin=solver,
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_tag_mock.assert_called_once_with('new-tag', strict=False)
        get_groups_mock.assert_called_once_with('new-tag', inherit=False)
        get_inheritance_mock.assert_called_once_with('new-tag')
        get_external_repos_mock.assert_called_once_with(tag_info='new-tag')
        create_mock.assert_called_once()
        set_extras_mock.assert_called_once_with('new-tag', extra={})

    def test_tag_creation_with_complex_settings(self):
        """Test creating a tag with all settings."""
        inheritance = [create_inheritance_link('parent-tag', 10)]
        external_repos = [create_inheritance_link('external-repo', 5)]
        groups = {'build': ['package1', 'package2']}

        tag = create_test_tag(
            'complex-tag',
            locked=True,
            permission='admin',
            arches=['x86_64', 'aarch64'],
            maven_support=True,
            maven_include_all=True,
            extras={'key': 'value'},
            groups=groups,
            inheritance=inheritance,
            external_repos=external_repos
        )
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        get_tag_mock = Mock()
        get_tag_mock.return_value = None

        get_groups_mock = Mock()
        get_groups_mock.return_value = []

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        create_mock = Mock()
        create_mock.return_value = None

        set_extras_mock = Mock()
        set_extras_mock.return_value = None

        add_group_mock = Mock()
        add_group_mock.return_value = None

        add_group_pkg1_mock = Mock()
        add_group_pkg1_mock.return_value = None

        add_group_pkg2_mock = Mock()
        add_group_pkg2_mock.return_value = None

        add_inheritance_mock = Mock()
        add_inheritance_mock.return_value = None

        add_external_repo_mock = Mock()
        add_external_repo_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('createTag', create_mock)
        self.queue_client_response('editTag2', set_extras_mock)
        self.queue_client_response('addTagGroup', add_group_mock)
        self.queue_client_response('groupListAdd', add_group_pkg1_mock)
        self.queue_client_response('groupListAdd', add_group_pkg2_mock)
        self.queue_client_response('setInheritanceData', add_inheritance_mock)
        self.queue_client_response('addExternalRepoToTag', add_external_repo_mock)

        processor = Processor(
            koji_session=mock_session,
            stream_origin=solver,
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        # Verify all calls were made
        get_tag_mock.assert_called_once_with('complex-tag', strict=False)
        get_groups_mock.assert_called_once_with('complex-tag', inherit=False)
        get_inheritance_mock.assert_called_once_with('complex-tag')
        get_external_repos_mock.assert_called_once_with(tag_info='complex-tag')
        create_mock.assert_called_once()
        set_extras_mock.assert_called_once_with('complex-tag', extra={'key': 'value'})
        add_group_mock.assert_called_once_with('complex-tag', 'build')
        add_group_pkg1_mock.assert_called_once_with('complex-tag', 'build', 'package1')
        add_group_pkg2_mock.assert_called_once_with('complex-tag', 'build', 'package2')
        add_inheritance_mock.assert_called_once()
        add_external_repo_mock.assert_called_once_with('complex-tag', 'external-repo', 5)

    def test_tag_update_locked_status(self):
        """Test updating an existing tag's locked status."""
        tag = create_test_tag('existing-tag', locked=True)
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        # Mock the getTag call to return existing tag with different locked status
        get_tag_mock = Mock()
        get_tag_mock.return_value = {
            'name': 'existing-tag',
            'locked': False,  # Currently unlocked
            'permission': None,
            'arches': [],
            'maven_support': False,
            'maven_include_all': False,
            'extras': {}
        }

        get_groups_mock = Mock()
        get_groups_mock.return_value = []

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        set_locked_mock = Mock()
        set_locked_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('editTag2', set_locked_mock)

        processor = Processor(
            koji_session=mock_session,
            stream_origin=solver,
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_tag_mock.assert_called_once_with('existing-tag', strict=False)
        set_locked_mock.assert_called_once_with('existing-tag', locked=True)

    def test_tag_update_permission(self):
        """Test updating an existing tag's permission."""
        tag = create_test_tag('existing-tag', permission='admin')
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        # Mock the getTag call to return existing tag with different permission
        get_tag_mock = Mock()
        get_tag_mock.return_value = {
            'name': 'existing-tag',
            'locked': False,
            'permission': None,  # Currently no permission
            'arches': [],
            'maven_support': False,
            'maven_include_all': False,
            'extras': {}
        }

        get_groups_mock = Mock()
        get_groups_mock.return_value = []

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        set_permission_mock = Mock()
        set_permission_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('editTag2', set_permission_mock)

        processor = Processor(
            koji_session=mock_session,
            stream_origin=solver,
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_tag_mock.assert_called_once_with('existing-tag', strict=False)
        set_permission_mock.assert_called_once_with('existing-tag', perm='admin')

    def test_tag_update_arches(self):
        """Test updating an existing tag's architectures."""
        tag = create_test_tag('existing-tag', arches=['x86_64', 'aarch64'])
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        # Mock the getTag call to return existing tag with different arches
        get_tag_mock = Mock()
        get_tag_mock.return_value = {
            'name': 'existing-tag',
            'locked': False,
            'permission': None,
            'arches': ['x86_64'],  # Currently only x86_64
            'maven_support': False,
            'maven_include_all': False,
            'extras': {}
        }

        get_groups_mock = Mock()
        get_groups_mock.return_value = []

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        set_arches_mock = Mock()
        set_arches_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('editTag2', set_arches_mock)

        processor = Processor(
            koji_session=mock_session,
            stream_origin=solver,
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_tag_mock.assert_called_once_with('existing-tag', strict=False)
        set_arches_mock.assert_called_once_with('existing-tag', arches='x86_64 aarch64')

    def test_tag_update_maven_settings(self):
        """Test updating an existing tag's maven settings."""
        tag = create_test_tag('existing-tag', maven_support=True, maven_include_all=True)
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        # Mock the getTag call to return existing tag with different maven settings
        get_tag_mock = Mock()
        get_tag_mock.return_value = {
            'name': 'existing-tag',
            'locked': False,
            'permission': None,
            'arches': [],
            'maven_support': False,  # Currently disabled
            'maven_include_all': False,  # Currently disabled
            'extras': {}
        }

        get_groups_mock = Mock()
        get_groups_mock.return_value = []

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        set_maven_mock = Mock()
        set_maven_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('editTag2', set_maven_mock)

        processor = Processor(
            koji_session=mock_session,
            stream_origin=solver,
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_tag_mock.assert_called_once_with('existing-tag', strict=False)
        set_maven_mock.assert_called_once_with('existing-tag', maven_support=True, maven_include_all=True)

    def test_tag_add_group(self):
        """Test adding a group to an existing tag."""
        groups = {'build': ['package1']}
        tag = create_test_tag('existing-tag', groups=groups)
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        # Mock the getTag call to return existing tag
        get_tag_mock = Mock()
        get_tag_mock.return_value = {
            'name': 'existing-tag',
            'locked': False,
            'permission': None,
            'arches': [],
            'maven_support': False,
            'maven_include_all': False,
            'extras': {}
        }

        get_groups_mock = Mock()
        get_groups_mock.return_value = []  # No groups currently

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        add_group_mock = Mock()
        add_group_mock.return_value = None

        add_group_pkg_mock = Mock()
        add_group_pkg_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('addTagGroup', add_group_mock)
        self.queue_client_response('groupListAdd', add_group_pkg_mock)

        processor = Processor(
            koji_session=mock_session,
            stream_origin=solver,
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_tag_mock.assert_called_once_with('existing-tag', strict=False)
        add_group_mock.assert_called_once_with('existing-tag', 'build')
        add_group_pkg_mock.assert_called_once_with('existing-tag', 'build', 'package1')

    def test_tag_add_inheritance(self):
        """Test adding inheritance to an existing tag."""
        inheritance = [create_inheritance_link('parent-tag', 10)]
        tag = create_test_tag('existing-tag', inheritance=inheritance)
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        # Mock the getTag call to return existing tag
        get_tag_mock = Mock()
        get_tag_mock.return_value = {
            'name': 'existing-tag',
            'locked': False,
            'permission': None,
            'arches': [],
            'maven_support': False,
            'maven_include_all': False,
            'extras': {}
        }

        get_groups_mock = Mock()
        get_groups_mock.return_value = []

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []  # No inheritance currently

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        add_inheritance_mock = Mock()
        add_inheritance_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('setInheritanceData', add_inheritance_mock)

        processor = Processor(
            koji_session=mock_session,
            stream_origin=solver,
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_tag_mock.assert_called_once_with('existing-tag', strict=False)
        add_inheritance_mock.assert_called_once()

    def test_tag_add_external_repo(self):
        """Test adding external repository to an existing tag."""
        external_repos = [create_inheritance_link('external-repo', 5)]
        tag = create_test_tag('existing-tag', external_repos=external_repos)
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        # Mock the getTag call to return existing tag
        get_tag_mock = Mock()
        get_tag_mock.return_value = {
            'name': 'existing-tag',
            'locked': False,
            'permission': None,
            'arches': [],
            'maven_support': False,
            'maven_include_all': False,
            'extras': {}
        }

        get_groups_mock = Mock()
        get_groups_mock.return_value = []

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []  # No external repos currently

        add_external_repo_mock = Mock()
        add_external_repo_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('addExternalRepoToTag', add_external_repo_mock)

        processor = Processor(
            koji_session=mock_session,
            stream_origin=solver,
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_tag_mock.assert_called_once_with('existing-tag', strict=False)
        add_external_repo_mock.assert_called_once_with('existing-tag', 'external-repo', 5)

    def test_tag_no_changes_needed(self):
        """Test tag that already matches desired state."""
        tag = create_test_tag('existing-tag', locked=False, arches=['x86_64'])
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        # Mock the getTag call to return tag that already matches desired state
        get_tag_mock = Mock()
        get_tag_mock.return_value = {
            'name': 'existing-tag',
            'locked': False,  # Already matches
            'permission': None,
            'arches': ['x86_64'],  # Already matches
            'maven_support': False,
            'maven_include_all': False,
            'extras': {}
        }

        get_groups_mock = Mock()
        get_groups_mock.return_value = []

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)

        processor = Processor(
            koji_session=mock_session,
            stream_origin=solver,
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_tag_mock.assert_called_once_with('existing-tag', strict=False)
        get_groups_mock.assert_called_once_with('existing-tag', inherit=False)
        get_inheritance_mock.assert_called_once_with('existing-tag')
        get_external_repos_mock.assert_called_once_with(tag_info='existing-tag')

    def test_processor_summary_with_multiple_tags(self):
        """Test that the processor summary is correct with multiple tags."""
        tags = [
            create_test_tag('tag1', locked=True, arches=['x86_64']),
            create_test_tag('tag2', permission='admin', maven_support=True)
        ]
        solver = create_solver_with_objects(tags)
        mock_session = create_test_koji_session()

        # Mock getTag calls to return None (tags don't exist)
        get_tag1_mock = Mock()
        get_tag1_mock.return_value = None

        get_tag2_mock = Mock()
        get_tag2_mock.return_value = None

        # Mock other calls
        get_groups1_mock = Mock()
        get_groups1_mock.return_value = []

        get_groups2_mock = Mock()
        get_groups2_mock.return_value = []

        get_inheritance1_mock = Mock()
        get_inheritance1_mock.return_value = []

        get_inheritance2_mock = Mock()
        get_inheritance2_mock.return_value = []

        get_external_repos1_mock = Mock()
        get_external_repos1_mock.return_value = []

        get_external_repos2_mock = Mock()
        get_external_repos2_mock.return_value = []

        # Mock createTag calls for tag creation
        create1_mock = Mock()
        create1_mock.return_value = None

        create2_mock = Mock()
        create2_mock.return_value = None

        # Mock setExtras calls
        set_extras1_mock = Mock()
        set_extras1_mock.return_value = None

        set_extras2_mock = Mock()
        set_extras2_mock.return_value = None

        # Queue responses for both tags
        self.queue_client_response('getTag', get_tag1_mock)
        self.queue_client_response('getTagGroups', get_groups1_mock)
        self.queue_client_response('getInheritanceData', get_inheritance1_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos1_mock)
        self.queue_client_response('createTag', create1_mock)
        self.queue_client_response('editTag2', set_extras1_mock)

        self.queue_client_response('getTag', get_tag2_mock)
        self.queue_client_response('getTagGroups', get_groups2_mock)
        self.queue_client_response('getInheritanceData', get_inheritance2_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos2_mock)
        self.queue_client_response('createTag', create2_mock)
        self.queue_client_response('editTag2', set_extras2_mock)

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
        get_tag1_mock.assert_called_once_with('tag1', strict=False)
        get_tag2_mock.assert_called_once_with('tag2', strict=False)
        create1_mock.assert_called_once()
        create2_mock.assert_called_once()
        set_extras1_mock.assert_called_once_with('tag1', extra={})
        set_extras2_mock.assert_called_once_with('tag2', extra={})


# The end.

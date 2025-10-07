"""
koji-habitude - test_processor_models.test_tag

Unit tests for processor integration with tag models and change reporting.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

from unittest import TestCase
from unittest.mock import Mock

from koji_habitude.models import Tag
from koji_habitude.models.tag import ExternalRepoLink, InheritanceLink
from koji_habitude.processor import (
    DiffOnlyProcessor,
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


def create_test_tag(name: str, locked: bool = False, permission: str = None,
                   arches: list = None, maven_support: bool = False,
                   maven_include_all: bool = False, extras: dict = None,
                   groups: dict = None, inheritance: list = None,
                   external_repos: list = None, packages: list = None) -> Tag:
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
        packages: List of package entries (default empty list)

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
        packages=packages or [],
        filename='test.yaml',
        lineno=1
    )


def create_inheritance_link(name: str, priority: int = None) -> InheritanceLink:
    """Create an inheritance link for testing."""
    return InheritanceLink(name=name, priority=priority)


def create_external_repo_link(name: str, priority: int = None) -> ExternalRepoLink:
    """Create an external repo link for testing."""
    return ExternalRepoLink(name=name, priority=priority)


class TestProcessorTagLifecycle(MulticallMocking, TestCase):
    """
    Test Tag processor integration for tag lifecycle operations.

    Covers tag creation, property updates, and scenarios where no changes are needed.
    """

    def test_creation(self):
        """Test creating a new tag with basic settings."""
        tag = create_test_tag('new-tag', locked=False, arches=['x86_64'])
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        get_tag_mock = Mock()
        get_tag_mock.return_value = None

        get_tag_post_mock = Mock()
        get_tag_post_mock.return_value = None

        list_packages_mock = Mock()
        list_packages_mock.return_value = []

        get_groups_mock = Mock()
        get_groups_mock.return_value = []

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        create_mock = Mock()
        create_mock.return_value = None


        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('listPackages', list_packages_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('createTag', create_mock)
        self.queue_client_response('getTag', get_tag_post_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_tag_mock.assert_called_once_with('new-tag', strict=False)
        get_tag_post_mock.assert_called_once_with('new-tag', strict=False)
        # When tag doesn't exist, deferred calls are not made
        list_packages_mock.assert_not_called()
        get_groups_mock.assert_not_called()
        get_inheritance_mock.assert_not_called()
        get_external_repos_mock.assert_not_called()
        create_mock.assert_called_once()

    def test_creation_with_complex_settings(self):
        """Test creating a tag with all settings."""
        inheritance = [create_inheritance_link('parent-tag', 10)]
        external_repos = [create_external_repo_link('external-repo', 5)]
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

        get_tag_post_mock = Mock()
        get_tag_post_mock.return_value = None

        list_packages_mock = Mock()
        list_packages_mock.return_value = []

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

        set_permission_mock = Mock()
        set_permission_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('listPackages', list_packages_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('createTag', create_mock)
        self.queue_client_response('editTag2', set_permission_mock)
        self.queue_client_response('editTag2', set_extras_mock)
        self.queue_client_response('groupListAdd', add_group_mock)
        self.queue_client_response('groupPackageListAdd', add_group_pkg1_mock)
        self.queue_client_response('groupPackageListAdd', add_group_pkg2_mock)
        self.queue_client_response('setInheritanceData', add_inheritance_mock)
        self.queue_client_response('addExternalRepoToTag', add_external_repo_mock)
        self.queue_client_response('getTag', get_tag_post_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_resolver_with_objects({
                ('tag', 'parent-tag'): {'id': 123, 'name': 'parent-tag'}
            }),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        # Verify all calls were made
        get_tag_mock.assert_called_once_with('complex-tag', strict=False)
        get_tag_post_mock.assert_called_once_with('complex-tag', strict=False)
        # When tag doesn't exist, deferred calls are not made
        list_packages_mock.assert_not_called()
        get_groups_mock.assert_not_called()
        get_inheritance_mock.assert_not_called()
        get_external_repos_mock.assert_not_called()
        create_mock.assert_called_once()
        set_permission_mock.assert_called_once_with('complex-tag', perm='admin')
        set_extras_mock.assert_called_once_with('complex-tag', extra={'key': 'value'})
        add_group_mock.assert_called_once_with('complex-tag', 'build', description=None, block=False, force=True)
        add_group_pkg1_mock.assert_called_once_with('complex-tag', 'build', 'package1', block=False, force=True)
        add_group_pkg2_mock.assert_called_once_with('complex-tag', 'build', 'package2', block=False, force=True)
        add_inheritance_mock.assert_called_once_with(
            'complex-tag',
            [
                {
                    'parent_id': 123,
                    'priority': 10,
                    'intransitive': False,
                    'maxdepth': None,
                    'noconfig': False,
                    'pkg_filter': '',
                }
            ])
        add_external_repo_mock.assert_called_once_with('complex-tag', 'external-repo', priority=5, merge_mode='koji', arches=None)

    def test_update_locked_status(self):
        """Test updating an existing tag's locked status."""
        tag = create_test_tag('existing-tag', locked=True)
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        # Mock the getTag call to return existing tag with different locked status
        get_tag_mock = Mock()
        get_tag_mock.return_value = {
            'name': 'existing-tag',
            'locked': False,  # Currently unlocked
            'perm': None,
            'arches': '',
            'maven_support': False,
            'maven_include_all': False,
            'extra': {}
        }

        list_packages_mock = Mock()
        list_packages_mock.return_value = []

        get_groups_mock = Mock()
        get_groups_mock.return_value = []

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        set_locked_mock = Mock()
        set_locked_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('listPackages', list_packages_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('editTag2', set_locked_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        list_packages_mock.assert_called_once_with(tagID='existing-tag')
        get_tag_mock.assert_called_once_with('existing-tag', strict=False)
        set_locked_mock.assert_called_once_with('existing-tag', locked=True)

    def test_update_permission(self):
        """Test updating an existing tag's permission."""
        tag = create_test_tag('existing-tag', permission='admin')
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        # Mock the getTag call to return existing tag with different permission
        get_tag_mock = Mock()
        get_tag_mock.return_value = {
            'name': 'existing-tag',
            'locked': False,
            'perm': None,  # Currently no permission
            'arches': '',
            'maven_support': False,
            'maven_include_all': False,
            'extra': {}
        }

        list_packages_mock = Mock()
        list_packages_mock.return_value = []

        get_groups_mock = Mock()
        get_groups_mock.return_value = []

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        set_permission_mock = Mock()
        set_permission_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('listPackages', list_packages_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('editTag2', set_permission_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        list_packages_mock.assert_called_once_with(tagID='existing-tag')
        get_tag_mock.assert_called_once_with('existing-tag', strict=False)
        set_permission_mock.assert_called_once_with('existing-tag', perm='admin')

    def test_update_arches(self):
        """Test updating an existing tag's architectures."""
        tag = create_test_tag('existing-tag', arches=['x86_64', 'aarch64'])
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        # Mock the getTag call to return existing tag with different arches
        get_tag_mock = Mock()
        get_tag_mock.return_value = {
            'name': 'existing-tag',
            'locked': False,
            'perm': None,
            'arches': 'x86_64',  # Currently only x86_64
            'maven_support': False,
            'maven_include_all': False,
            'extra': {}
        }

        list_packages_mock = Mock()
        list_packages_mock.return_value = []

        get_groups_mock = Mock()
        get_groups_mock.return_value = []

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        set_arches_mock = Mock()
        set_arches_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('listPackages', list_packages_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('editTag2', set_arches_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        list_packages_mock.assert_called_once_with(tagID='existing-tag')
        get_tag_mock.assert_called_once_with('existing-tag', strict=False)
        set_arches_mock.assert_called_once_with('existing-tag', arches='x86_64 aarch64')

    def test_update_maven_settings(self):
        """Test updating an existing tag's maven settings."""
        tag = create_test_tag('existing-tag', maven_support=True, maven_include_all=True)
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        # Mock the getTag call to return existing tag with different maven settings
        get_tag_mock = Mock()
        get_tag_mock.return_value = {
            'name': 'existing-tag',
            'locked': False,
            'perm': None,
            'arches': '',
            'maven_support': False,  # Currently disabled
            'maven_include_all': False,  # Currently disabled
            'extra': {}
        }

        list_packages_mock = Mock()
        list_packages_mock.return_value = []

        get_groups_mock = Mock()
        get_groups_mock.return_value = []

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        set_maven_mock = Mock()
        set_maven_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('listPackages', list_packages_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('editTag2', set_maven_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        list_packages_mock.assert_called_once_with(tagID='existing-tag')
        get_tag_mock.assert_called_once_with('existing-tag', strict=False)
        set_maven_mock.assert_called_once_with('existing-tag', maven_support=True, maven_include_all=True)

    def test_no_changes_needed(self):
        """Test tag that already matches desired state."""
        tag = create_test_tag('existing-tag', locked=False, arches=['x86_64'])
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        # Mock the getTag call to return tag that already matches desired state
        get_tag_mock = Mock()
        get_tag_mock.return_value = {
            'name': 'existing-tag',
            'locked': False,  # Already matches
            'perm': None,
            'arches': 'x86_64',  # Already matches
            'maven_support': False,
            'maven_include_all': False,
            'extra': {}
        }

        list_packages_mock = Mock()
        list_packages_mock.return_value = []

        get_groups_mock = Mock()
        get_groups_mock.return_value = []

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('listPackages', list_packages_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_tag_mock.assert_called_once_with('existing-tag', strict=False)
        list_packages_mock.assert_called_once_with(tagID='existing-tag')
        get_groups_mock.assert_called_once_with('existing-tag', inherit=False, incl_blocked=True)
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

        get_tag_post1_mock = Mock()
        get_tag_post1_mock.return_value = None

        get_tag_post2_mock = Mock()
        get_tag_post2_mock.return_value = None

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

        set_permission2_mock = Mock()
        set_permission2_mock.return_value = None

        # Queue responses for both tags
        self.queue_client_response('getTag', get_tag1_mock)
        self.queue_client_response('getTagGroups', get_groups1_mock)
        self.queue_client_response('getInheritanceData', get_inheritance1_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos1_mock)
        self.queue_client_response('createTag', create1_mock)

        self.queue_client_response('getTag', get_tag2_mock)
        self.queue_client_response('getTagGroups', get_groups2_mock)
        self.queue_client_response('getInheritanceData', get_inheritance2_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos2_mock)
        self.queue_client_response('createTag', create2_mock)
        self.queue_client_response('editTag2', set_permission2_mock)

        self.queue_client_response('getTag', get_tag_post1_mock)
        self.queue_client_response('getTag', get_tag_post2_mock)

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
        get_tag1_mock.assert_called_once_with('tag1', strict=False)
        get_tag2_mock.assert_called_once_with('tag2', strict=False)
        create1_mock.assert_called_once()
        create2_mock.assert_called_once()
        get_tag_post1_mock.assert_called_once_with('tag1', strict=False)
        get_tag_post2_mock.assert_called_once_with('tag2', strict=False)
        set_permission2_mock.assert_called_once_with('tag2', perm='admin')


class TestProcessorTagGroups(MulticallMocking, TestCase):
    """
    Test Tag processor integration for group and package management.

    Covers adding, updating, and removing groups and packages within groups.
    """

    def test_add_group(self):
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
            'perm': None,
            'arches': '',
            'maven_support': False,
            'maven_include_all': False,
            'extra': {}
        }

        list_packages_mock = Mock()
        list_packages_mock.return_value = []

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
        self.queue_client_response('listPackages', list_packages_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('groupListAdd', add_group_mock)
        self.queue_client_response('groupPackageListAdd', add_group_pkg_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_tag_mock.assert_called_once_with('existing-tag', strict=False)
        list_packages_mock.assert_called_once_with(tagID='existing-tag')
        get_groups_mock.assert_called_once_with('existing-tag', inherit=False, incl_blocked=True)
        add_group_mock.assert_called_once_with('existing-tag', 'build', description=None, block=False, force=True)
        add_group_pkg_mock.assert_called_once_with('existing-tag', 'build', 'package1', block=False, force=True)

    def test_update_existing_group(self):
        """Test updating an existing group's properties."""
        groups = {'build': ['package1']}
        tag = create_test_tag('existing-tag', groups=groups)
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        # Mock the getTag call to return existing tag
        get_tag_mock = Mock()
        get_tag_mock.return_value = {
            'name': 'existing-tag',
            'locked': False,
            'perm': None,
            'arches': '',
            'maven_support': False,
            'maven_include_all': False,
            'extra': {}
        }

        list_packages_mock = Mock()
        list_packages_mock.return_value = []

        # Mock existing group with different properties
        get_groups_mock = Mock()
        get_groups_mock.return_value = [{
            'name': 'build',
            'description': 'Old description',
            'blocked': True,  # Different from our desired state
            'packagelist': [{'package': 'package1', 'blocked': False}]
        }]

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        update_group_mock = Mock()
        update_group_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('listPackages', list_packages_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('groupListAdd', update_group_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_tag_mock.assert_called_once_with('existing-tag', strict=False)
        list_packages_mock.assert_called_once_with(tagID='existing-tag')
        get_groups_mock.assert_called_once_with('existing-tag', inherit=False, incl_blocked=True)
        # Should update group because block status differs
        update_group_mock.assert_called_once_with('existing-tag', 'build', description=None, block=False, force=True)

    def test_remove_group(self):
        """Test removing a group from an existing tag."""
        # Tag with no groups (desired state)
        tag = create_test_tag('existing-tag', groups={})
        # Set exact_groups to True so removal happens
        tag.exact_groups = True
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        # Mock the getTag call to return existing tag
        get_tag_mock = Mock()
        get_tag_mock.return_value = {
            'name': 'existing-tag',
            'locked': False,
            'perm': None,
            'arches': '',
            'maven_support': False,
            'maven_include_all': False,
            'extra': {}
        }

        list_packages_mock = Mock()
        list_packages_mock.return_value = []

        # Mock existing group that should be removed
        get_groups_mock = Mock()
        get_groups_mock.return_value = [{
            'name': 'build',
            'description': 'Build group',
            'blocked': False,
            'packagelist': []
        }]

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        remove_group_mock = Mock()
        remove_group_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('listPackages', list_packages_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('groupListRemove', remove_group_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_tag_mock.assert_called_once_with('existing-tag', strict=False)
        list_packages_mock.assert_called_once_with(tagID='existing-tag')
        get_groups_mock.assert_called_once_with('existing-tag', inherit=False, incl_blocked=True)
        # Should remove the group because exact_groups=True and group not in desired state
        remove_group_mock.assert_called_once_with('existing-tag', 'build')

    def test_add_package_to_existing_group(self):
        """Test adding a package to an existing group."""
        groups = {'build': ['package1', 'package2']}
        tag = create_test_tag('existing-tag', groups=groups)
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        # Mock the getTag call to return existing tag
        get_tag_mock = Mock()
        get_tag_mock.return_value = {
            'name': 'existing-tag',
            'locked': False,
            'perm': None,
            'arches': '',
            'maven_support': False,
            'maven_include_all': False,
            'extra': {}
        }

        list_packages_mock = Mock()
        list_packages_mock.return_value = []

        # Mock existing group with only one package
        get_groups_mock = Mock()
        get_groups_mock.return_value = [{
            'name': 'build',
            'description': None,
            'blocked': False,
            'packagelist': [{'package': 'package1', 'blocked': False}]
        }]

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        add_group_pkg_mock = Mock()
        add_group_pkg_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('listPackages', list_packages_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('groupPackageListAdd', add_group_pkg_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_tag_mock.assert_called_once_with('existing-tag', strict=False)
        list_packages_mock.assert_called_once_with(tagID='existing-tag')
        get_groups_mock.assert_called_once_with('existing-tag', inherit=False, incl_blocked=True)
        # Should add the missing package
        add_group_pkg_mock.assert_called_once_with('existing-tag', 'build', 'package2', block=False, force=True)

    def test_update_package_in_group(self):
        """Test updating a package's block status in an existing group."""
        groups = {'build': [{'name': 'package1', 'block': True}]}
        tag = create_test_tag('existing-tag', groups=groups)
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        # Mock the getTag call to return existing tag
        get_tag_mock = Mock()
        get_tag_mock.return_value = {
            'name': 'existing-tag',
            'locked': False,
            'perm': None,
            'arches': '',
            'maven_support': False,
            'maven_include_all': False,
            'extra': {}
        }

        list_packages_mock = Mock()
        list_packages_mock.return_value = []

        # Mock existing group with package that has different block status
        get_groups_mock = Mock()
        get_groups_mock.return_value = [{
            'name': 'build',
            'description': None,
            'blocked': False,
            'packagelist': [{'package': 'package1', 'blocked': False}]  # Currently not blocked
        }]

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        update_group_pkg_mock = Mock()
        update_group_pkg_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('listPackages', list_packages_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('groupPackageListAdd', update_group_pkg_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_tag_mock.assert_called_once_with('existing-tag', strict=False)
        list_packages_mock.assert_called_once_with(tagID='existing-tag')
        get_groups_mock.assert_called_once_with('existing-tag', inherit=False, incl_blocked=True)
        # Should update the package because block status differs
        update_group_pkg_mock.assert_called_once_with('existing-tag', 'build', 'package1', block=True, force=True)

    def test_remove_package_from_group(self):
        """Test removing a package from an existing group."""
        groups = {'build': ['package1']}  # Only package1 desired
        tag = create_test_tag('existing-tag', groups=groups)
        # Set exact_packages to True so removal happens
        tag.groups['build'].exact_packages = True
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        # Mock the getTag call to return existing tag
        get_tag_mock = Mock()
        get_tag_mock.return_value = {
            'name': 'existing-tag',
            'locked': False,
            'perm': None,
            'arches': '',
            'maven_support': False,
            'maven_include_all': False,
            'extra': {}
        }

        list_packages_mock = Mock()
        list_packages_mock.return_value = []

        # Mock existing group with extra package that should be removed
        get_groups_mock = Mock()
        get_groups_mock.return_value = [{
            'name': 'build',
            'description': None,
            'blocked': False,
            'packagelist': [
                {'package': 'package1', 'blocked': False},
                {'package': 'package2', 'blocked': False}  # Should be removed
            ]
        }]

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        remove_group_pkg_mock = Mock()
        remove_group_pkg_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('listPackages', list_packages_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('groupPackageListRemove', remove_group_pkg_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_tag_mock.assert_called_once_with('existing-tag', strict=False)
        list_packages_mock.assert_called_once_with(tagID='existing-tag')
        get_groups_mock.assert_called_once_with('existing-tag', inherit=False, incl_blocked=True)
        # Should remove the extra package because exact_packages=True
        remove_group_pkg_mock.assert_called_once_with('existing-tag', 'build', 'package2')

    def test_mixed_package_changes(self):
        """Test applying multiple package changes in one operation."""
        groups = {
            'build': [
                'package1',  # Keep existing
                'package3',  # Add new
                {'name': 'package4', 'block': True}  # Add new with block
            ]
        }
        tag = create_test_tag('existing-tag', groups=groups)
        # Set exact_packages to True so removals happen
        tag.groups['build'].exact_packages = True
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        # Mock the getTag call to return existing tag
        get_tag_mock = Mock()
        get_tag_mock.return_value = {
            'name': 'existing-tag',
            'locked': False,
            'perm': None,
            'arches': '',
            'maven_support': False,
            'maven_include_all': False,
            'extra': {}
        }

        list_packages_mock = Mock()
        list_packages_mock.return_value = []

        # Mock existing group with packages that need various changes
        get_groups_mock = Mock()
        get_groups_mock.return_value = [{
            'name': 'build',
            'description': None,
            'blocked': False,
            'packagelist': [
                {'package': 'package1', 'blocked': False},  # Keep as-is
                {'package': 'package2', 'blocked': False},  # Remove (not in desired state)
                {'package': 'package4', 'blocked': False}   # Update block status
            ]
        }]

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        add_group_pkg3_mock = Mock()
        add_group_pkg3_mock.return_value = None

        update_group_pkg4_mock = Mock()
        update_group_pkg4_mock.return_value = None

        remove_group_pkg2_mock = Mock()
        remove_group_pkg2_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('listPackages', list_packages_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('groupPackageListAdd', add_group_pkg3_mock)
        self.queue_client_response('groupPackageListAdd', update_group_pkg4_mock)
        self.queue_client_response('groupPackageListRemove', remove_group_pkg2_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_tag_mock.assert_called_once_with('existing-tag', strict=False)
        list_packages_mock.assert_called_once_with(tagID='existing-tag')
        get_groups_mock.assert_called_once_with('existing-tag', inherit=False, incl_blocked=True)

        # Should add new package3
        add_group_pkg3_mock.assert_called_once_with('existing-tag', 'build', 'package3', block=False, force=True)
        # Should update package4 block status
        update_group_pkg4_mock.assert_called_once_with('existing-tag', 'build', 'package4', block=True, force=True)
        # Should remove package2
        remove_group_pkg2_mock.assert_called_once_with('existing-tag', 'build', 'package2')


class TestProcessorTagDependencies(MulticallMocking, TestCase):
    """
    Test Tag processor integration for dependency management.

    Covers inheritance and external repository management.
    """

    def test_add_inheritance(self):
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
            'perm': None,
            'arches': '',
            'maven_support': False,
            'maven_include_all': False,
            'extra': {}
        }

        list_packages_mock = Mock()
        list_packages_mock.return_value = []

        get_groups_mock = Mock()
        get_groups_mock.return_value = []

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []  # No inheritance currently

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        add_inheritance_mock = Mock()
        add_inheritance_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('listPackages', list_packages_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('setInheritanceData', add_inheritance_mock)

        resolver = create_resolver_with_objects({
            ('tag', 'parent-tag'): {'id': 1, 'name': 'parent-tag'},
        })

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=resolver,
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_tag_mock.assert_called_once_with('existing-tag', strict=False)
        add_inheritance_mock.assert_called_once()

    def test_add_external_repo(self):
        """Test adding external repository to an existing tag."""
        external_repos = [create_external_repo_link('external-repo', 5)]
        tag = create_test_tag('existing-tag', external_repos=external_repos)
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        # Mock the getTag call to return existing tag
        get_tag_mock = Mock()
        get_tag_mock.return_value = {
            'name': 'existing-tag',
            'locked': False,
            'perm': None,
            'arches': '',
            'maven_support': False,
            'maven_include_all': False,
            'extra': {}
        }

        list_packages_mock = Mock()
        list_packages_mock.return_value = []

        get_groups_mock = Mock()
        get_groups_mock.return_value = []

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []  # No external repos currently

        add_external_repo_mock = Mock()
        add_external_repo_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('listPackages', list_packages_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('addExternalRepoToTag', add_external_repo_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_tag_mock.assert_called_once_with('existing-tag', strict=False)
        add_external_repo_mock.assert_called_once_with('existing-tag', 'external-repo', priority=5, merge_mode='koji', arches=None)

    def test_simultaneous_tag_creation_with_inheritance(self):
        """
        Test creating two tags simultaneously where one inherits from the other.

        This verifies that dependency resolution correctly handles the case where
        both parent and child tags are created in the same processing run, with
        the parent tag being processed first due to dependency ordering.
        """
        # Create parent tag
        parent_tag = create_test_tag('parent-tag', locked=False, arches=['x86_64'])

        # Create child tag that inherits from parent
        inheritance = [create_inheritance_link('parent-tag', 10)]
        child_tag = create_test_tag('child-tag', locked=False, arches=['x86_64'], inheritance=inheritance)

        # Create solver with both tags
        solver = create_solver_with_objects([parent_tag, child_tag])
        mock_session = create_test_koji_session()

        # Mock getTag calls - both tags don't exist yet
        get_parent_tag_mock = Mock()
        get_parent_tag_mock.return_value = None

        get_child_tag_mock = Mock()
        get_child_tag_mock.return_value = None

        # Mock getTagGroups calls
        get_parent_groups_mock = Mock()
        get_parent_groups_mock.return_value = []

        get_child_groups_mock = Mock()
        get_child_groups_mock.return_value = []

        # Mock getInheritanceData calls
        get_parent_inheritance_mock = Mock()
        get_parent_inheritance_mock.return_value = []

        get_child_inheritance_mock = Mock()
        get_child_inheritance_mock.return_value = []

        # Mock getTagExternalRepos calls
        get_parent_external_repos_mock = Mock()
        get_parent_external_repos_mock.return_value = []

        get_child_external_repos_mock = Mock()
        get_child_external_repos_mock.return_value = []

        # Mock createTag calls
        create_parent_mock = Mock()
        create_parent_mock.return_value = None

        create_child_mock = Mock()
        create_child_mock.return_value = None

        # Mock post-creation getTag calls
        get_parent_tag_post_mock = Mock()
        get_parent_tag_post_mock.return_value = None

        get_child_tag_post_mock = Mock()
        get_child_tag_post_mock.return_value = None

        # Mock editTag2 calls (for setExtras)
        edit_parent_tag_mock = Mock()
        edit_parent_tag_mock.return_value = None

        edit_child_tag_mock = Mock()
        edit_child_tag_mock.return_value = None

        # Mock setInheritanceData call for child tag inheritance
        set_child_inheritance_mock = Mock()
        set_child_inheritance_mock.return_value = None

        # Queue all the mock responses in dependency order
        # Parent tag processing first
        self.queue_client_response('getTag', get_parent_tag_mock)
        self.queue_client_response('getTagGroups', get_parent_groups_mock)
        self.queue_client_response('getInheritanceData', get_parent_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_parent_external_repos_mock)
        self.queue_client_response('createTag', create_parent_mock)
        self.queue_client_response('editTag2', edit_parent_tag_mock)
        self.queue_client_response('getTag', get_parent_tag_post_mock)

        # Child tag processing second
        self.queue_client_response('getTag', get_child_tag_mock)
        self.queue_client_response('getTagGroups', get_child_groups_mock)
        self.queue_client_response('getInheritanceData', get_child_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_child_external_repos_mock)
        self.queue_client_response('createTag', create_child_mock)
        self.queue_client_response('editTag2', edit_child_tag_mock)
        self.queue_client_response('setInheritanceData', set_child_inheritance_mock)
        self.queue_client_response('getTag', get_child_tag_post_mock)

        # Create resolver with both tags to handle dependency resolution
        resolver = create_resolver_with_objects({
            ('tag', 'parent-tag'): {'id': 1, 'name': 'parent-tag'},
            ('tag', 'child-tag'): {'id': 2, 'name': 'child-tag'},
        })

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=resolver,
            chunk_size=10
        )

        # Process both tags - should handle dependency resolution correctly
        result = processor.step()
        self.assertTrue(result)  # Should process both objects
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        # Verify parent tag was created first
        create_parent_mock.assert_called_once_with(
            'parent-tag',
            locked=False,
            arches='x86_64',
            maven_support=False,
            maven_include_all=False
        )

        # Verify child tag was created second
        create_child_mock.assert_called_once_with(
            'child-tag',
            locked=False,
            arches='x86_64',
            maven_support=False,
            maven_include_all=False
        )

        # Verify inheritance was set on child tag
        set_child_inheritance_mock.assert_called_once()
        inheritance_call = set_child_inheritance_mock.call_args
        self.assertEqual(inheritance_call[0][0], 'child-tag')  # tag name
        # Verify the inheritance data structure
        inheritance_data = inheritance_call[0][1]
        self.assertEqual(len(inheritance_data), 1)
        self.assertEqual(inheritance_data[0]['parent_id'], 1)  # parent tag ID
        self.assertEqual(inheritance_data[0]['priority'], 10)


class TestProcessorTagPackages(MulticallMocking, TestCase):
    """
    Test Tag processor integration for package list management.

    Covers adding, updating, blocking/unblocking, and removing packages from tags.
    """

    def test_add_package_to_tag(self):
        """Test adding a single package to an existing tag."""

        tag = create_test_tag(
            'existing-tag',
            packages=[{'name': 'my-package', 'owner': 'testuser'}])
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        # Mock the getTag call to return existing tag
        get_tag_mock = Mock()
        get_tag_mock.return_value = {
            'name': 'existing-tag',
            'locked': False,
            'perm': None,
            'arches': '',
            'maven_support': False,
            'maven_include_all': False,
            'extra': {}
        }

        list_packages_mock = Mock()
        list_packages_mock.return_value = []  # No packages currently

        get_groups_mock = Mock()
        get_groups_mock.return_value = []

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        add_package_mock = Mock()
        add_package_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('listPackages', list_packages_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('packageListAdd', add_package_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_tag_mock.assert_called_once_with('existing-tag', strict=False)
        list_packages_mock.assert_called_once_with(tagID='existing-tag')
        add_package_mock.assert_called_once_with(
            'existing-tag',
            'my-package',
            owner='testuser',
            block=False,
            extra_arches=None,
            force=True
        )

    def test_add_package_with_extra_arches(self):
        """Test adding a package with extra_arches specified."""

        tag = create_test_tag('existing-tag', packages=[{'name': 'my-package', 'owner': 'testuser', 'extra-arches': ['i686', 'ppc64le']}])
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        # Mock the getTag call to return existing tag
        get_tag_mock = Mock()
        get_tag_mock.return_value = {
            'name': 'existing-tag',
            'locked': False,
            'perm': None,
            'arches': '',
            'maven_support': False,
            'maven_include_all': False,
            'extra': {}
        }

        list_packages_mock = Mock()
        list_packages_mock.return_value = []

        get_groups_mock = Mock()
        get_groups_mock.return_value = []

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        add_package_mock = Mock()
        add_package_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('listPackages', list_packages_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('packageListAdd', add_package_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        add_package_mock.assert_called_once_with(
            'existing-tag',
            'my-package',
            owner='testuser',
            block=False,
            extra_arches='i686 ppc64le',
            force=True
        )

    def test_block_package(self):
        """Test blocking an existing unblocked package."""

        tag = create_test_tag('existing-tag', packages=[{'name': 'my-package', 'owner': 'testuser', 'blocked': True}])
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        # Mock the getTag call to return existing tag
        get_tag_mock = Mock()
        get_tag_mock.return_value = {
            'name': 'existing-tag',
            'locked': False,
            'perm': None,
            'arches': '',
            'maven_support': False,
            'maven_include_all': False,
            'extra': {}
        }

        list_packages_mock = Mock()
        list_packages_mock.return_value = [{
            'package_name': 'my-package',
            'owner_name': 'testuser',
            'blocked': False,  # Currently not blocked
            'extra_arches': None
        }]

        get_groups_mock = Mock()
        get_groups_mock.return_value = []

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        block_package_mock = Mock()
        block_package_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('listPackages', list_packages_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('packageListBlock', block_package_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        list_packages_mock.assert_called_once_with(tagID='existing-tag')
        block_package_mock.assert_called_once_with('existing-tag', 'my-package', force=True)

    def test_unblock_package(self):
        """Test unblocking a previously blocked package."""

        tag = create_test_tag(
            'existing-tag',
            packages=[{'name': 'my-package', 'owner': 'testuser', 'blocked': False}])
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        # Mock the getTag call to return existing tag
        get_tag_mock = Mock()
        get_tag_mock.return_value = {
            'name': 'existing-tag',
            'locked': False,
            'perm': None,
            'arches': '',
            'maven_support': False,
            'maven_include_all': False,
            'extra': {}
        }

        list_packages_mock = Mock()
        list_packages_mock.return_value = [{
            'package_name': 'my-package',
            'owner_name': 'testuser',
            'blocked': True,  # Currently blocked
            'extra_arches': None
        }]

        get_groups_mock = Mock()
        get_groups_mock.return_value = []

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        unblock_package_mock = Mock()
        unblock_package_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('listPackages', list_packages_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('packageListUnblock', unblock_package_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        unblock_package_mock.assert_called_once_with('existing-tag', 'my-package', force=True)

    def test_update_package_owner(self):
        """Test changing the owner of an existing package."""

        tag = create_test_tag('existing-tag', packages=[{'name': 'my-package', 'owner': 'newuser'}])
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        # Mock the getTag call to return existing tag
        get_tag_mock = Mock()
        get_tag_mock.return_value = {
            'name': 'existing-tag',
            'locked': False,
            'perm': None,
            'arches': '',
            'maven_support': False,
            'maven_include_all': False,
            'extra': {}
        }

        list_packages_mock = Mock()
        list_packages_mock.return_value = [{
            'package_name': 'my-package',
            'owner_name': 'olduser',  # Different owner
            'blocked': False,
            'extra_arches': None
        }]

        get_groups_mock = Mock()
        get_groups_mock.return_value = []

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        set_owner_mock = Mock()
        set_owner_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('listPackages', list_packages_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('packageListSetOwner', set_owner_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        set_owner_mock.assert_called_once_with('existing-tag', 'my-package', 'newuser', force=True)

    def test_update_package_extra_arches(self):
        """Test changing extra_arches of an existing package."""

        tag = create_test_tag('existing-tag', packages=[{'name': 'my-package', 'owner': 'testuser', 'extra-arches': ['i686']}])
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        # Mock the getTag call to return existing tag
        get_tag_mock = Mock()
        get_tag_mock.return_value = {
            'name': 'existing-tag',
            'locked': False,
            'perm': None,
            'arches': '',
            'maven_support': False,
            'maven_include_all': False,
            'extra': {}
        }

        list_packages_mock = Mock()
        list_packages_mock.return_value = [{
            'package_name': 'my-package',
            'owner_name': 'testuser',
            'blocked': False,
            'extra_arches': None  # Different from desired state
        }]

        get_groups_mock = Mock()
        get_groups_mock.return_value = []

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        set_arches_mock = Mock()
        set_arches_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('listPackages', list_packages_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('packageListSetArches', set_arches_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        # koji call expects arches to be a space separated string
        set_arches_mock.assert_called_once_with('existing-tag', 'my-package', 'i686', force=True)

    def test_remove_package_with_exact_packages(self):
        """Test removing packages not in desired state when exact_packages=True."""

        tag = create_test_tag('existing-tag', packages=[{'name': 'keep-package', 'owner': 'testuser'}])
        tag.exact_packages = True
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        # Mock the getTag call to return existing tag
        get_tag_mock = Mock()
        get_tag_mock.return_value = {
            'name': 'existing-tag',
            'locked': False,
            'perm': None,
            'arches': '',
            'maven_support': False,
            'maven_include_all': False,
            'extra': {}
        }

        list_packages_mock = Mock()
        list_packages_mock.return_value = [
            {
                'package_name': 'keep-package',
                'owner_name': 'testuser',
                'blocked': False,
                'extra_arches': None
            },
            {
                'package_name': 'remove-package',  # Should be removed
                'owner_name': 'testuser',
                'blocked': False,
                'extra_arches': None
            }
        ]

        get_groups_mock = Mock()
        get_groups_mock.return_value = []

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        remove_package_mock = Mock()
        remove_package_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('listPackages', list_packages_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('packageListRemove', remove_package_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        remove_package_mock.assert_called_once_with('existing-tag', 'remove-package', force=True)

    def test_no_package_removal_without_exact_packages(self):
        """Test that packages aren't removed when exact_packages=False."""

        tag = create_test_tag('existing-tag', packages=[{'name': 'keep-package', 'owner': 'testuser'}])
        tag.exact_packages = False  # Default behavior
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        # Mock the getTag call to return existing tag
        get_tag_mock = Mock()
        get_tag_mock.return_value = {
            'name': 'existing-tag',
            'locked': False,
            'perm': None,
            'arches': '',
            'maven_support': False,
            'maven_include_all': False,
            'extra': {}
        }

        list_packages_mock = Mock()
        list_packages_mock.return_value = [
            {
                'package_name': 'keep-package',
                'owner_name': 'testuser',
                'blocked': False,
                'extra_arches': None
            },
            {
                'package_name': 'extra-package',  # Should NOT be removed
                'owner_name': 'testuser',
                'blocked': False,
                'extra_arches': None
            }
        ]

        get_groups_mock = Mock()
        get_groups_mock.return_value = []

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('listPackages', list_packages_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        # No packageListRemove should have been queued
        # We verify this implicitly - if there was a call, it would fail because we didn't queue a mock for it

    def test_mixed_package_operations(self):
        """Test applying multiple package operations in one step."""

        tag = create_test_tag('existing-tag', packages=[
            {'name': 'keep-package', 'owner': 'testuser'},  # Keep as-is
            {'name': 'add-package', 'owner': 'testuser'},   # Add new
            {'name': 'update-owner-package', 'owner': 'newowner'},  # Update owner
            {'name': 'block-package', 'owner': 'testuser', 'blocked': True},  # Block
        ])
        tag.exact_packages = True
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        # Mock the getTag call to return existing tag
        get_tag_mock = Mock()
        get_tag_mock.return_value = {
            'name': 'existing-tag',
            'locked': False,
            'perm': None,
            'arches': '',
            'maven_support': False,
            'maven_include_all': False,
            'extra': {}
        }

        list_packages_mock = Mock()
        list_packages_mock.return_value = [
            {
                'package_name': 'keep-package',
                'owner_name': 'testuser',
                'blocked': False,
                'extra_arches': None
            },
            {
                'package_name': 'update-owner-package',
                'owner_name': 'oldowner',
                'blocked': False,
                'extra_arches': None
            },
            {
                'package_name': 'block-package',
                'owner_name': 'testuser',
                'blocked': False,  # Will be blocked
                'extra_arches': None
            },
            {
                'package_name': 'remove-package',
                'owner_name': 'testuser',
                'blocked': False,
                'extra_arches': None
            }
        ]

        get_groups_mock = Mock()
        get_groups_mock.return_value = []

        get_inheritance_mock = Mock()
        get_inheritance_mock.return_value = []

        get_external_repos_mock = Mock()
        get_external_repos_mock.return_value = []

        add_package_mock = Mock()
        add_package_mock.return_value = None

        set_owner_mock = Mock()
        set_owner_mock.return_value = None

        block_package_mock = Mock()
        block_package_mock.return_value = None

        remove_package_mock = Mock()
        remove_package_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('listPackages', list_packages_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('packageListAdd', add_package_mock)
        self.queue_client_response('packageListBlock', block_package_mock)
        self.queue_client_response('packageListSetOwner', set_owner_mock)
        self.queue_client_response('packageListRemove', remove_package_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        # Verify all operations were called
        add_package_mock.assert_called_once_with(
            'existing-tag',
            'add-package',
            owner='testuser',
            block=False,
            extra_arches=None,
            force=True
        )
        block_package_mock.assert_called_once_with('existing-tag', 'block-package', force=True)
        set_owner_mock.assert_called_once_with('existing-tag', 'update-owner-package', 'newowner', force=True)
        remove_package_mock.assert_called_once_with('existing-tag', 'remove-package', force=True)

    def test_create_tag_with_packages(self):
        """Test creating a new tag with packages from the start."""

        tag = create_test_tag('new-tag', arches=['x86_64'], packages=[
            {'name': 'package1', 'owner': 'testuser'},
            {'name': 'package2', 'owner': 'testuser', 'blocked': True}
        ])
        solver = create_solver_with_objects([tag])
        mock_session = create_test_koji_session()

        get_tag_mock = Mock()
        get_tag_mock.return_value = None  # Tag doesn't exist

        get_tag_post_mock = Mock()
        get_tag_post_mock.return_value = None

        list_packages_mock = Mock()
        list_packages_mock.return_value = []

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

        add_package1_mock = Mock()
        add_package1_mock.return_value = None

        add_package2_mock = Mock()
        add_package2_mock.return_value = None

        self.queue_client_response('getTag', get_tag_mock)
        self.queue_client_response('listPackages', list_packages_mock)
        self.queue_client_response('getTagGroups', get_groups_mock)
        self.queue_client_response('getInheritanceData', get_inheritance_mock)
        self.queue_client_response('getTagExternalRepos', get_external_repos_mock)
        self.queue_client_response('createTag', create_mock)
        self.queue_client_response('editTag2', set_extras_mock)
        self.queue_client_response('packageListAdd', add_package1_mock)
        self.queue_client_response('packageListAdd', add_package2_mock)
        self.queue_client_response('getTag', get_tag_post_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_tag_mock.assert_called_once_with('new-tag', strict=False)
        create_mock.assert_called_once()
        # Verify both packages were added during creation
        add_package1_mock.assert_called_once_with(
            'new-tag',
            'package1',
            owner='testuser',
            block=False,
            extra_arches=None,
            force=True
        )
        add_package2_mock.assert_called_once_with(
            'new-tag',
            'package2',
            owner='testuser',
            block=True,
            extra_arches=None,
            force=True
        )


# The end.

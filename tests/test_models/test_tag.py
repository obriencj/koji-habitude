"""
koji-habitude - test_tag

Unit tests for koji_habitude.models.Tag.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

import unittest

from koji_habitude.models import Tag


class TestTagModelCore(unittest.TestCase):
    """
    Test core Tag model functionality - creation, defaults, and splitting.
    """

    def test_tag_creation_with_defaults(self):
        """
        Test Tag creation with default values.
        """

        data = {'type': 'tag', 'name': 'test-tag'}
        tag = Tag.from_dict(data)

        self.assertEqual(tag.typename, 'tag')
        self.assertEqual(tag.name, 'test-tag')
        self.assertEqual(tag.arches, [])
        self.assertFalse(tag.maven_support)
        self.assertFalse(tag.maven_include_all)
        self.assertEqual(tag.extras, {})
        self.assertEqual(tag.groups, {})
        self.assertEqual(tag.inheritance, [])
        self.assertEqual(tag.external_repos, [])
        self.assertTrue(tag.can_split())

    def test_tag_creation_with_all_fields(self):
        """
        Test Tag creation with all fields specified.
        """

        data = {
            'type': 'tag',
            'name': 'test-tag',
            'arches': ['x86_64', 'i686'],
            'maven-support': True,
            'maven-include-all': True,
            'extras': {'key1': 'value1', 'key2': 'value2'},
            'groups': {'group1': ['pkg1', 'pkg2']},
            'inheritance': [
                {'name': 'parent1', 'priority': 10},
                {'name': 'parent2', 'priority': 20}
            ],
            'external-repos': [
                {'name': 'repo1', 'priority': 30},
                {'name': 'repo2', 'priority': 40}
            ]
        }
        tag = Tag.from_dict(data)

        self.assertEqual(tag.arches, ['x86_64', 'i686'])
        self.assertTrue(tag.maven_support)
        self.assertTrue(tag.maven_include_all)
        self.assertEqual(tag.extras, {'key1': 'value1', 'key2': 'value2'})

        # Check groups structure (now TagGroup objects instead of simple lists)
        self.assertEqual(len(tag.groups), 1)
        self.assertIn('group1', tag.groups)
        group1 = tag.groups['group1']
        self.assertEqual(group1.name, 'group1')
        self.assertEqual(len(group1.packages), 2)
        self.assertEqual(group1.packages[0].name, 'pkg1')
        self.assertEqual(group1.packages[0].type, 'package')
        self.assertEqual(group1.packages[0].block, False)
        self.assertEqual(group1.packages[1].name, 'pkg2')
        self.assertEqual(group1.packages[1].type, 'package')
        self.assertEqual(group1.packages[1].block, False)

        # Check inheritance links (now separate field)
        self.assertEqual(len(tag.inheritance), 2)
        self.assertEqual(tag.inheritance[0].name, 'parent1')
        self.assertEqual(tag.inheritance[0].priority, 10)
        self.assertEqual(tag.inheritance[1].name, 'parent2')
        self.assertEqual(tag.inheritance[1].priority, 20)

        # Check external repo links (now separate field)
        self.assertEqual(len(tag.external_repos), 2)
        self.assertEqual(tag.external_repos[0].name, 'repo1')
        self.assertEqual(tag.external_repos[0].priority, 30)
        self.assertEqual(tag.external_repos[1].name, 'repo2')
        self.assertEqual(tag.external_repos[1].priority, 40)

    def test_tag_split(self):
        """
        Test Tag splitting functionality.
        """

        data = {
            'type': 'tag',
            'name': 'test-tag',
            'arches': ['x86_64'],
            'maven-support': True,
            'inheritance': [
                {'name': 'parent', 'priority': 10}
            ],
            'external-repos': [
                {'name': 'repo', 'priority': 30}
            ]
        }
        tag = Tag.from_dict(data)

        split_tag = tag.split()
        self.assertIsInstance(split_tag, Tag)
        self.assertEqual(split_tag.name, 'test-tag')
        self.assertEqual(split_tag.arches, ['x86_64'])
        # Inheritance and external repos should not be included in split (dependency data)
        self.assertEqual(split_tag.inheritance, [])
        self.assertEqual(split_tag.external_repos, [])


class TestTagModelInheritanceField(unittest.TestCase):
    """
    Test Tag model inheritance field validation and simplified format conversion.
    """

    def test_tag_inheritance_simple_string_list(self):
        """
        Test Tag creation with inheritance as a simple list of strings.
        Strings should be converted to tag inheritance with incrementing priorities.
        """

        data = {
            'type': 'tag',
            'name': 'test-tag',
            'inheritance': ['parent1', 'parent2', 'parent3']
        }
        tag = Tag.from_dict(data)

        # Check that inheritance was converted to full objects
        self.assertEqual(len(tag.inheritance), 3)

        # Check first parent (priority 0)
        self.assertEqual(tag.inheritance[0].name, 'parent1')
        self.assertEqual(tag.inheritance[0].priority, 0)

        # Check second parent (priority 10)
        self.assertEqual(tag.inheritance[1].name, 'parent2')
        self.assertEqual(tag.inheritance[1].priority, 10)

        # Check third parent (priority 20)
        self.assertEqual(tag.inheritance[2].name, 'parent3')
        self.assertEqual(tag.inheritance[2].priority, 20)

    def test_tag_inheritance_mixed_string_and_dict_list(self):
        """
        Test Tag creation with inheritance mixing strings and dict objects.
        Strings should be converted to tag inheritance, dicts should be used as-is.
        """

        data = {
            'type': 'tag',
            'name': 'test-tag',
            'inheritance': [
                'parent1',  # String - should become tag with priority 0
                {'name': 'parent2', 'priority': 50},  # Dict with explicit priority
                'parent3',  # String - should become tag with priority 10
            ]
        }
        tag = Tag.from_dict(data)

        # Check that inheritance was processed correctly
        self.assertEqual(len(tag.inheritance), 3)

        # Check string conversion (parent1)
        self.assertEqual(tag.inheritance[0].name, 'parent1')
        self.assertEqual(tag.inheritance[0].priority, 0)

        # Check dict with explicit priority (parent2)
        self.assertEqual(tag.inheritance[1].name, 'parent2')
        self.assertEqual(tag.inheritance[1].priority, 50)

        # Check string conversion (parent3) - priority should increment from max existing
        self.assertEqual(tag.inheritance[2].name, 'parent3')
        self.assertEqual(tag.inheritance[2].priority, 60)  # 50 + 10

    def test_tag_inheritance_empty_list(self):
        """
        Test Tag creation with empty inheritance list.
        """

        data = {
            'type': 'tag',
            'name': 'test-tag',
            'inheritance': []
        }
        tag = Tag.from_dict(data)

        # Check that inheritance is empty
        self.assertEqual(len(tag.inheritance), 0)


class TestTagModelExternalReposField(unittest.TestCase):
    """
    Test Tag model external-repos field validation and simplified format conversion.
    """

    def test_tag_external_repos_simple_string_list(self):
        """
        Test Tag creation with external-repos as a simple list of strings.
        Strings should be converted to external repo links with incrementing priorities.
        """

        data = {
            'type': 'tag',
            'name': 'test-tag',
            'external-repos': ['repo1', 'repo2', 'repo3']
        }
        tag = Tag.from_dict(data)

        # Check that external repos were converted to full objects
        self.assertEqual(len(tag.external_repos), 3)

        # Check first repo (priority 0)
        self.assertEqual(tag.external_repos[0].name, 'repo1')
        self.assertEqual(tag.external_repos[0].priority, 0)

        # Check second repo (priority 10)
        self.assertEqual(tag.external_repos[1].name, 'repo2')
        self.assertEqual(tag.external_repos[1].priority, 10)

        # Check third repo (priority 20)
        self.assertEqual(tag.external_repos[2].name, 'repo3')
        self.assertEqual(tag.external_repos[2].priority, 20)

    def test_tag_external_repos_mixed_string_and_dict_list(self):
        """
        Test Tag creation with external-repos mixing strings and dict objects.
        Strings should be converted to external repo links, dicts should be used as-is.
        """

        data = {
            'type': 'tag',
            'name': 'test-tag',
            'external-repos': [
                'repo1',  # String - should become repo with priority 0
                {'name': 'repo2', 'priority': 50, 'merge-mode': 'simple'},  # Dict with explicit priority
                'repo3',  # String - should become repo with priority 10
            ]
        }
        tag = Tag.from_dict(data)

        # Check that external repos were processed correctly
        self.assertEqual(len(tag.external_repos), 3)

        # Check string conversion (repo1)
        self.assertEqual(tag.external_repos[0].name, 'repo1')
        self.assertEqual(tag.external_repos[0].priority, 0)
        self.assertEqual(tag.external_repos[0].merge_mode, 'koji')  # default

        # Check dict with explicit priority (repo2)
        self.assertEqual(tag.external_repos[1].name, 'repo2')
        self.assertEqual(tag.external_repos[1].priority, 50)
        self.assertEqual(tag.external_repos[1].merge_mode, 'simple')

        # Check string conversion (repo3) - priority should increment from max existing
        self.assertEqual(tag.external_repos[2].name, 'repo3')
        self.assertEqual(tag.external_repos[2].priority, 60)  # 50 + 10

    def test_tag_external_repos_empty_list(self):
        """
        Test Tag creation with empty external-repos list.
        """

        data = {
            'type': 'tag',
            'name': 'test-tag',
            'external-repos': []
        }
        tag = Tag.from_dict(data)

        # Check that external repos is empty
        self.assertEqual(len(tag.external_repos), 0)

    def test_tag_external_repos_with_arches(self):
        """
        Test Tag creation with external repos that have arch specifications.
        """

        data = {
            'type': 'tag',
            'name': 'test-tag',
            'external-repos': [
                {'name': 'repo1', 'priority': 10, 'arches': ['x86_64', 'i686']},
                {'name': 'repo2', 'priority': 20, 'merge-mode': 'simple'}
            ]
        }
        tag = Tag.from_dict(data)

        # Check first repo with arches
        self.assertEqual(tag.external_repos[0].name, 'repo1')
        self.assertEqual(tag.external_repos[0].priority, 10)
        self.assertEqual(tag.external_repos[0].arches, ['x86_64', 'i686'])
        self.assertEqual(tag.external_repos[0].merge_mode, 'koji')  # default

        # Check second repo with merge mode
        self.assertEqual(tag.external_repos[1].name, 'repo2')
        self.assertEqual(tag.external_repos[1].priority, 20)
        self.assertEqual(tag.external_repos[1].arches, None)  # default
        self.assertEqual(tag.external_repos[1].merge_mode, 'simple')


class TestTagModelGroupsField(unittest.TestCase):
    """
    Test Tag model groups field validation, formats, and error handling.
    """

    def test_tag_groups_dict_format(self):
        """
        Test Tag creation with groups in dict format: {'group_name': ['pkg1', 'pkg2']}
        """

        data = {
            'type': 'tag',
            'name': 'test-tag',
            'groups': {'build': ['package1', 'package2'], 'srpm': ['source1']}
        }
        tag = Tag.from_dict(data)

        # Check groups structure
        self.assertEqual(len(tag.groups), 2)

        # Check build group
        self.assertIn('build', tag.groups)
        build_group = tag.groups['build']
        self.assertEqual(build_group.name, 'build')
        self.assertEqual(len(build_group.packages), 2)
        self.assertEqual(build_group.packages[0].name, 'package1')
        self.assertEqual(build_group.packages[0].type, 'package')
        self.assertEqual(build_group.packages[0].block, False)
        self.assertEqual(build_group.packages[1].name, 'package2')
        self.assertEqual(build_group.packages[1].type, 'package')
        self.assertEqual(build_group.packages[1].block, False)

        # Check srpm group
        self.assertIn('srpm', tag.groups)
        srpm_group = tag.groups['srpm']
        self.assertEqual(srpm_group.name, 'srpm')
        self.assertEqual(len(srpm_group.packages), 1)
        self.assertEqual(srpm_group.packages[0].name, 'source1')
        self.assertEqual(srpm_group.packages[0].type, 'package')
        self.assertEqual(srpm_group.packages[0].block, False)

    def test_tag_groups_list_format(self):
        """
        Test Tag creation with groups in list format: [{'name': 'group', 'packages': ['pkg']}]
        """

        data = {
            'type': 'tag',
            'name': 'test-tag',
            'groups': [
                {'name': 'build', 'packages': ['package1', 'package2']},
                {'name': 'srpm', 'packages': ['source1']}
            ]
        }
        tag = Tag.from_dict(data)

        # Check groups structure
        self.assertEqual(len(tag.groups), 2)

        # Check build group
        self.assertIn('build', tag.groups)
        build_group = tag.groups['build']
        self.assertEqual(build_group.name, 'build')
        self.assertEqual(len(build_group.packages), 2)
        self.assertEqual(build_group.packages[0].name, 'package1')
        self.assertEqual(build_group.packages[1].name, 'package2')

        # Check srpm group
        self.assertIn('srpm', tag.groups)
        srpm_group = tag.groups['srpm']
        self.assertEqual(srpm_group.name, 'srpm')
        self.assertEqual(len(srpm_group.packages), 1)
        self.assertEqual(srpm_group.packages[0].name, 'source1')

    def test_tag_groups_dict_with_package_objects(self):
        """
        Test Tag creation with groups containing package objects with type and block.
        """

        data = {
            'type': 'tag',
            'name': 'test-tag',
            'groups': {
                'build': {
                    'packages': [
                        'package1',  # Simple string
                        {'name': 'package2', 'type': 'package', 'block': False},
                        {'name': '@group1', 'type': 'group', 'block': True}
                    ]
                }
            }
        }
        tag = Tag.from_dict(data)

        # Check groups structure
        self.assertEqual(len(tag.groups), 1)

        # Check build group
        build_group = tag.groups['build']
        self.assertEqual(build_group.name, 'build')
        self.assertEqual(len(build_group.packages), 3)

        # First package (simple string)
        self.assertEqual(build_group.packages[0].name, 'package1')
        self.assertEqual(build_group.packages[0].type, 'package')
        self.assertEqual(build_group.packages[0].block, False)

        # Second package (explicit dict)
        self.assertEqual(build_group.packages[1].name, 'package2')
        self.assertEqual(build_group.packages[1].type, 'package')
        self.assertEqual(build_group.packages[1].block, False)

        # Third package (group with @ prefix - name should keep the @ when specified explicitly)
        self.assertEqual(build_group.packages[2].name, '@group1')
        self.assertEqual(build_group.packages[2].type, 'group')
        self.assertEqual(build_group.packages[2].block, True)

    def test_tag_groups_string_package_with_at_prefix(self):
        """
        Test Tag creation with string packages that have @ prefix (indicating group type).
        """

        data = {
            'type': 'tag',
            'name': 'test-tag',
            'groups': {
                'build': ['package1', '@group1', 'package2', '@group2']
            }
        }
        tag = Tag.from_dict(data)

        # Check groups structure
        build_group = tag.groups['build']
        self.assertEqual(len(build_group.packages), 4)

        # First package (no @ prefix)
        self.assertEqual(build_group.packages[0].name, 'package1')
        self.assertEqual(build_group.packages[0].type, 'package')
        self.assertEqual(build_group.packages[0].block, False)

        # Second package (@ prefix)
        self.assertEqual(build_group.packages[1].name, '@group1')
        self.assertEqual(build_group.packages[1].type, 'group')
        self.assertEqual(build_group.packages[1].block, False)

        # Third package (no @ prefix)
        self.assertEqual(build_group.packages[2].name, 'package2')
        self.assertEqual(build_group.packages[2].type, 'package')
        self.assertEqual(build_group.packages[2].block, False)

        # Fourth package (@ prefix)
        self.assertEqual(build_group.packages[3].name, '@group2')
        self.assertEqual(build_group.packages[3].type, 'group')
        self.assertEqual(build_group.packages[3].block, False)

    def test_tag_groups_duplicate_group_names_error(self):
        """
        Test that duplicate group names in list format raise an error.
        """

        data = {
            'type': 'tag',
            'name': 'test-tag',
            'groups': [
                {'name': 'build', 'packages': ['package1']},
                {'name': 'build', 'packages': ['package2']}  # Duplicate name
            ]
        }

        with self.assertRaises(TypeError) as context:
            Tag.from_dict(data)

        self.assertIn('Duplicate group build', str(context.exception))

    def test_tag_groups_invalid_string_in_dict_error(self):
        """
        Test that string values in dict format raise an error.
        """

        data = {
            'type': 'tag',
            'name': 'test-tag',
            'groups': {
                'build': 'package1'  # String instead of list/dict
            }
        }

        with self.assertRaises(ValueError) as context:
            Tag.from_dict(data)

        self.assertIn('Group build must be a dictionary or list', str(context.exception))

    def test_tag_groups_invalid_data_type_error(self):
        """
        Test that invalid data types for groups raise an error.
        """

        data = {
            'type': 'tag',
            'name': 'test-tag',
            'groups': 'invalid'  # String instead of dict/list
        }

        with self.assertRaises(ValueError) as context:
            Tag.from_dict(data)

        self.assertIn('Groups must be a dictionary or list', str(context.exception))


class TestTagModelPackagesField(unittest.TestCase):
    """
    Test Tag model packages field validation and simplified format conversion.
    """

    def test_tag_packages_simple_string_list(self):
        """
        Test Tag creation with packages as a simple list of strings.
        """

        data = {
            'type': 'tag',
            'name': 'test-tag',
            'packages': ['package1', 'package2', 'package3']
        }
        tag = Tag.from_dict(data)

        # Check that packages were converted to PackageEntry objects
        self.assertEqual(len(tag.packages), 3)

        # Check first package
        self.assertEqual(tag.packages[0].name, 'package1')
        self.assertEqual(tag.packages[0].block, False)
        self.assertEqual(tag.packages[0].owner, None)
        self.assertEqual(tag.packages[0].extra_arches, None)

        # Check second package
        self.assertEqual(tag.packages[1].name, 'package2')
        self.assertEqual(tag.packages[1].block, False)
        self.assertEqual(tag.packages[1].owner, None)
        self.assertEqual(tag.packages[1].extra_arches, None)

        # Check third package
        self.assertEqual(tag.packages[2].name, 'package3')
        self.assertEqual(tag.packages[2].block, False)
        self.assertEqual(tag.packages[2].owner, None)
        self.assertEqual(tag.packages[2].extra_arches, None)

    def test_tag_packages_dict_format(self):
        """
        Test Tag creation with packages in dict format with full specifications.
        """

        data = {
            'type': 'tag',
            'name': 'test-tag',
            'packages': [
                {'name': 'package1', 'owner': 'user1'},
                {'name': 'package2', 'owner': 'user2', 'blocked': True},
                {'name': 'package3', 'owner': 'user3', 'extra-arches': ['i686', 'ppc64le']}
            ]
        }
        tag = Tag.from_dict(data)

        # Check packages structure
        self.assertEqual(len(tag.packages), 3)

        # Check first package (with owner)
        self.assertEqual(tag.packages[0].name, 'package1')
        self.assertEqual(tag.packages[0].owner, 'user1')
        self.assertEqual(tag.packages[0].block, False)
        self.assertEqual(tag.packages[0].extra_arches, None)

        # Check second package (with owner and blocked)
        self.assertEqual(tag.packages[1].name, 'package2')
        self.assertEqual(tag.packages[1].owner, 'user2')
        self.assertEqual(tag.packages[1].block, True)
        self.assertEqual(tag.packages[1].extra_arches, None)

        # Check third package (with owner and extra-arches)
        self.assertEqual(tag.packages[2].name, 'package3')
        self.assertEqual(tag.packages[2].owner, 'user3')
        self.assertEqual(tag.packages[2].block, False)
        self.assertEqual(tag.packages[2].extra_arches, ['i686', 'ppc64le'])

    def test_tag_packages_mixed_format(self):
        """
        Test Tag creation with packages mixing strings and dict objects.
        """

        data = {
            'type': 'tag',
            'name': 'test-tag',
            'packages': [
                'package1',  # Simple string
                {'name': 'package2', 'owner': 'user2'},  # Dict with owner
                'package3',  # Simple string
                {'name': 'package4', 'owner': 'user4', 'blocked': True}  # Dict with owner and blocked
            ]
        }
        tag = Tag.from_dict(data)

        # Check that packages were processed correctly
        self.assertEqual(len(tag.packages), 4)

        # Check string conversion (package1)
        self.assertEqual(tag.packages[0].name, 'package1')
        self.assertEqual(tag.packages[0].owner, None)
        self.assertEqual(tag.packages[0].block, False)

        # Check dict with owner (package2)
        self.assertEqual(tag.packages[1].name, 'package2')
        self.assertEqual(tag.packages[1].owner, 'user2')
        self.assertEqual(tag.packages[1].block, False)

        # Check string conversion (package3)
        self.assertEqual(tag.packages[2].name, 'package3')
        self.assertEqual(tag.packages[2].owner, None)
        self.assertEqual(tag.packages[2].block, False)

        # Check dict with owner and blocked (package4)
        self.assertEqual(tag.packages[3].name, 'package4')
        self.assertEqual(tag.packages[3].owner, 'user4')
        self.assertEqual(tag.packages[3].block, True)

    def test_tag_packages_empty_list(self):
        """
        Test Tag creation with empty packages list.
        """

        data = {
            'type': 'tag',
            'name': 'test-tag',
            'packages': []
        }
        tag = Tag.from_dict(data)

        # Check that packages is empty
        self.assertEqual(len(tag.packages), 0)

    def test_tag_packages_default_empty(self):
        """
        Test that packages defaults to empty list when not specified.
        """

        data = {
            'type': 'tag',
            'name': 'test-tag'
        }
        tag = Tag.from_dict(data)

        # Check that packages defaults to empty
        self.assertEqual(len(tag.packages), 0)
        self.assertEqual(tag.packages, [])

    def test_tag_packages_with_extra_arches(self):
        """
        Test Tag creation with packages that have extra-arches specified.
        """

        data = {
            'type': 'tag',
            'name': 'test-tag',
            'packages': [
                {'name': 'package1', 'owner': 'user1', 'extra-arches': ['x86_64', 'i686']},
                {'name': 'package2', 'owner': 'user2', 'extra-arches': ['ppc64le']}
            ]
        }
        tag = Tag.from_dict(data)

        # Check first package with multiple arches
        self.assertEqual(tag.packages[0].name, 'package1')
        self.assertEqual(tag.packages[0].owner, 'user1')
        self.assertEqual(tag.packages[0].extra_arches, ['x86_64', 'i686'])

        # Check second package with single arch
        self.assertEqual(tag.packages[1].name, 'package2')
        self.assertEqual(tag.packages[1].owner, 'user2')
        self.assertEqual(tag.packages[1].extra_arches, ['ppc64le'])

    def test_tag_packages_blocked_flag(self):
        """
        Test Tag creation with packages that have blocked flag set.
        """

        data = {
            'type': 'tag',
            'name': 'test-tag',
            'packages': [
                {'name': 'package1', 'owner': 'user1', 'blocked': False},
                {'name': 'package2', 'owner': 'user2', 'blocked': True},
                {'name': 'package3', 'owner': 'user3'}  # blocked defaults to False
            ]
        }
        tag = Tag.from_dict(data)

        # Check first package (explicitly not blocked)
        self.assertEqual(tag.packages[0].name, 'package1')
        self.assertEqual(tag.packages[0].block, False)

        # Check second package (blocked)
        self.assertEqual(tag.packages[1].name, 'package2')
        self.assertEqual(tag.packages[1].block, True)

        # Check third package (default not blocked)
        self.assertEqual(tag.packages[2].name, 'package3')
        self.assertEqual(tag.packages[2].block, False)


class TestTagModelDependencyResolution(unittest.TestCase):
    """
    Test Tag model dependency key generation for resolver.
    """

    def test_tag_dependency_keys(self):
        """
        Test Tag dependency resolution.
        """

        data = {
            'type': 'tag',
            'name': 'test-tag',
            'inheritance': [
                {'name': 'parent1', 'priority': 10},
                {'name': 'parent2', 'priority': 20}
            ],
            'external-repos': [
                {'name': 'repo1', 'priority': 30},
                {'name': 'repo2', 'priority': 40}
            ]
        }
        tag = Tag.from_dict(data)

        deps = tag.dependency_keys()
        expected = [
            ('tag', 'parent1'),
            ('tag', 'parent2'),
            ('external-repo', 'repo1'),
            ('external-repo', 'repo2')
        ]
        self.assertEqual(deps, expected)

    def test_tag_dependency_keys_empty(self):
        """
        Test Tag dependency resolution with no inheritance or external repos.
        """

        data = {'type': 'tag', 'name': 'test-tag'}
        tag = Tag.from_dict(data)

        deps = tag.dependency_keys()
        self.assertEqual(deps, [])

    def test_tag_dependency_keys_with_package_owners(self):
        """
        Test Tag dependency resolution includes package owners.
        """

        data = {
            'type': 'tag',
            'name': 'test-tag',
            'packages': [
                {'name': 'package1', 'owner': 'user1'},
                {'name': 'package2', 'owner': 'user2'},
                {'name': 'package3'}  # No owner
            ]
        }
        tag = Tag.from_dict(data)

        deps = tag.dependency_keys()
        expected = [
            ('user', 'user1'),
            ('user', 'user2')
        ]
        self.assertEqual(deps, expected)

    def test_tag_dependency_keys_with_all_dependencies(self):
        """
        Test Tag dependency resolution with packages, inheritance, and external repos.
        """

        data = {
            'type': 'tag',
            'name': 'test-tag',
            'packages': [
                {'name': 'package1', 'owner': 'user1'},
                {'name': 'package2', 'owner': 'user2'}
            ],
            'inheritance': [
                {'name': 'parent1', 'priority': 10}
            ],
            'external-repos': [
                {'name': 'repo1', 'priority': 30}
            ]
        }
        tag = Tag.from_dict(data)

        deps = tag.dependency_keys()
        expected = [
            ('tag', 'parent1'),
            ('external-repo', 'repo1'),
            ('user', 'user1'),
            ('user', 'user2')
        ]
        self.assertEqual(deps, expected)


# The end.

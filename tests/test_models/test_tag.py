"""
koji-habitude - test_tag

Unit tests for koji_habitude.models.Tag.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

import unittest

from koji_habitude.models import Tag


class TestTagModel(unittest.TestCase):
    """
    Test the Tag model.
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
                {'name': 'parent1', 'type': 'tag', 'priority': 10},
                {'name': 'parent2', 'type': 'tag', 'priority': 20},
                {'name': 'repo1', 'type': 'external-repo', 'priority': 30},
                {'name': 'repo2', 'type': 'external-repo', 'priority': 40}
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

        # Check inheritance links (unified list)
        self.assertEqual(len(tag.inheritance), 4)

        # Check parent tags (filtered by type)
        parent_tags = tag.parent_tags
        self.assertEqual(len(parent_tags), 2)
        self.assertEqual(parent_tags[0].name, 'parent1')
        self.assertEqual(parent_tags[0].type, 'tag')
        self.assertEqual(parent_tags[0].priority, 10)
        self.assertEqual(parent_tags[1].name, 'parent2')
        self.assertEqual(parent_tags[1].type, 'tag')
        self.assertEqual(parent_tags[1].priority, 20)

        # Check external repo links (filtered by type)
        external_repos = tag.external_repos
        self.assertEqual(len(external_repos), 2)
        self.assertEqual(external_repos[0].name, 'repo1')
        self.assertEqual(external_repos[0].type, 'external-repo')
        self.assertEqual(external_repos[0].priority, 30)
        self.assertEqual(external_repos[1].name, 'repo2')
        self.assertEqual(external_repos[1].type, 'external-repo')
        self.assertEqual(external_repos[1].priority, 40)

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
                {'name': 'parent', 'type': 'tag', 'priority': 10},
                {'name': 'repo', 'type': 'external-repo', 'priority': 30}
            ]
        }
        tag = Tag.from_dict(data)

        split_tag = tag.split()
        self.assertIsInstance(split_tag, Tag)
        self.assertEqual(split_tag.name, 'test-tag')
        self.assertEqual(split_tag.arches, ['x86_64'])
        # Inheritance should not be included in split (dependency data)
        self.assertEqual(split_tag.inheritance, [])
        # Properties should return empty lists when inheritance is empty
        self.assertEqual(split_tag.parent_tags, [])
        self.assertEqual(split_tag.external_repos, [])

    def test_tag_dependency_keys(self):
        """
        Test Tag dependency resolution.
        """

        data = {
            'type': 'tag',
            'name': 'test-tag',
            'inheritance': [
                {'name': 'parent1', 'type': 'tag', 'priority': 10},
                {'name': 'parent2', 'type': 'tag', 'priority': 20},
                {'name': 'repo1', 'type': 'external-repo', 'priority': 30},
                {'name': 'repo2', 'type': 'external-repo', 'priority': 40}
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

    def test_tag_inheritance_property_filtering(self):
        """
        Test that parent_tags and external_repos properties correctly filter inheritance by type.
        """

        data = {
            'type': 'tag',
            'name': 'test-tag',
            'inheritance': [
                {'name': 'parent1', 'type': 'tag', 'priority': 10},
                {'name': 'repo1', 'type': 'external-repo', 'priority': 30},
                {'name': 'parent2', 'type': 'tag', 'priority': 20},
                {'name': 'repo2', 'type': 'external-repo', 'priority': 40}
            ]
        }
        tag = Tag.from_dict(data)

        # Check that all inheritance items are present
        self.assertEqual(len(tag.inheritance), 4)

        # Check parent_tags property filters correctly
        parent_tags = tag.parent_tags
        self.assertEqual(len(parent_tags), 2)
        self.assertEqual(parent_tags[0].name, 'parent1')
        self.assertEqual(parent_tags[0].type, 'tag')
        self.assertEqual(parent_tags[1].name, 'parent2')
        self.assertEqual(parent_tags[1].type, 'tag')

        # Check external_repos property filters correctly
        external_repos = tag.external_repos
        self.assertEqual(len(external_repos), 2)
        self.assertEqual(external_repos[0].name, 'repo1')
        self.assertEqual(external_repos[0].type, 'external-repo')
        self.assertEqual(external_repos[1].name, 'repo2')
        self.assertEqual(external_repos[1].type, 'external-repo')

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
        self.assertEqual(tag.inheritance[0].type, 'tag')
        self.assertEqual(tag.inheritance[0].priority, 0)

        # Check second parent (priority 10)
        self.assertEqual(tag.inheritance[1].name, 'parent2')
        self.assertEqual(tag.inheritance[1].type, 'tag')
        self.assertEqual(tag.inheritance[1].priority, 10)

        # Check third parent (priority 20)
        self.assertEqual(tag.inheritance[2].name, 'parent3')
        self.assertEqual(tag.inheritance[2].type, 'tag')
        self.assertEqual(tag.inheritance[2].priority, 20)

        # Check parent_tags property returns all items (all are type 'tag')
        parent_tags = tag.parent_tags
        self.assertEqual(len(parent_tags), 3)
        self.assertEqual([p.name for p in parent_tags], ['parent1', 'parent2', 'parent3'])

        # Check external_repos property returns empty (no external repos)
        external_repos = tag.external_repos
        self.assertEqual(len(external_repos), 0)

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
                {'name': 'parent2', 'type': 'tag', 'priority': 50},  # Dict with explicit priority
                'parent3',  # String - should become tag with priority 10
                {'name': 'repo1', 'type': 'external-repo', 'priority': 25}  # Dict with different type
            ]
        }
        tag = Tag.from_dict(data)

        # Check that inheritance was processed correctly
        self.assertEqual(len(tag.inheritance), 4)

        # Check string conversion (parent1)
        self.assertEqual(tag.inheritance[0].name, 'parent1')
        self.assertEqual(tag.inheritance[0].type, 'tag')
        self.assertEqual(tag.inheritance[0].priority, 0)

        # Check dict with explicit priority (parent2)
        self.assertEqual(tag.inheritance[1].name, 'parent2')
        self.assertEqual(tag.inheritance[1].type, 'tag')
        self.assertEqual(tag.inheritance[1].priority, 50)

        # Check string conversion (parent3) - priority should increment from max existing
        self.assertEqual(tag.inheritance[2].name, 'parent3')
        self.assertEqual(tag.inheritance[2].type, 'tag')
        self.assertEqual(tag.inheritance[2].priority, 60)  # 50 + 10

        # Check dict with different type (repo1)
        self.assertEqual(tag.inheritance[3].name, 'repo1')
        self.assertEqual(tag.inheritance[3].type, 'external-repo')
        self.assertEqual(tag.inheritance[3].priority, 25)

        # Check property filtering
        parent_tags = tag.parent_tags
        self.assertEqual(len(parent_tags), 3)
        self.assertEqual([p.name for p in parent_tags], ['parent1', 'parent2', 'parent3'])

        external_repos = tag.external_repos
        self.assertEqual(len(external_repos), 1)
        self.assertEqual(external_repos[0].name, 'repo1')

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
        self.assertEqual(len(tag.parent_tags), 0)
        self.assertEqual(len(tag.external_repos), 0)

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


# The end.

"""
koji-habitude - test_data_models

Unit tests for data model conversion and validation.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

import pytest
from unittest.mock import Mock

from koji_habitude.models import CORE_MODELS
from koji_habitude.models.base import BaseKojiObject
from koji_habitude.models.user import User
from koji_habitude.models.tag import Tag
from koji_habitude.models.external_repo import ExternalRepo
from koji_habitude.models.target import Target
from koji_habitude.models.host import Host
from koji_habitude.models.group import Group
from koji_habitude.object_map import ObjectMap, OfflineResolver


class TestCoreModelsRegistry:
    """Test the core models registry."""

    def test_core_models_registry(self):
        """Test that all expected core models are registered."""

        expected_models = {
            'tag': Tag,
            'external-repo': ExternalRepo,
            'user': User,
            'target': Target,
            'host': Host,
            'group': Group,
        }

        assert CORE_MODELS == expected_models

    def test_all_models_inherit_from_base(self):
        """Test that all core models inherit from BaseKojiObject."""

        for model_type, model_class in CORE_MODELS.items():
            assert issubclass(model_class, BaseKojiObject)
            assert hasattr(model_class, 'dependent_keys')
            assert hasattr(model_class, '__init__')


class TestBaseKojiObject:
    """Test BaseKojiObject functionality."""

    def test_object_initialization(self):
        """Test basic object initialization."""

        data = {
            'type': 'user',
            'name': 'testuser',
            'description': 'Test user account'
        }

        obj = User(data)

        assert obj.type == 'user'
        assert obj.name == 'testuser'
        assert obj.data == data.copy()
        assert obj.key == ('user', 'testuser')

    def test_object_key_property(self):
        """Test object key property returns correct tuple."""

        data = {'type': 'tag', 'name': 'test-tag'}
        obj = Tag(data)

        assert obj.key == ('tag', 'test-tag')

    def test_object_equality(self):
        """Test object equality comparison."""

        data1 = {'type': 'user', 'name': 'testuser'}
        data2 = {'type': 'user', 'name': 'testuser'}
        data3 = {'type': 'user', 'name': 'otheruser'}

        obj1 = User(data1)
        obj2 = User(data2)
        obj3 = User(data3)

        assert obj1 == obj2
        assert obj1 != obj3
        assert obj2 != obj3

    def test_object_hash(self):
        """Test object hashing for use in sets/dicts."""

        data = {'type': 'user', 'name': 'testuser'}
        obj = User(data)

        # Should be hashable
        obj_set = {obj}
        assert obj in obj_set

        # Same key should hash the same
        data2 = {'type': 'user', 'name': 'testuser', 'extra': 'field'}
        obj2 = User(data2)
        assert hash(obj) == hash(obj2)

    def test_object_repr(self):
        """Test object string representation."""

        data = {'type': 'user', 'name': 'testuser'}
        obj = User(data)

        repr_str = repr(obj)
        assert 'User' in repr_str
        assert 'user' in repr_str
        assert 'testuser' in repr_str

    def test_dependents_resolution(self):
        """Test dependency resolution from object map."""

        # Create object map with dependencies
        obj_map = ObjectMap(OfflineResolver())

        # Create parent tag
        parent_data = {'type': 'tag', 'name': 'parent-tag'}
        parent_tag = Tag(parent_data)
        obj_map.add_object(parent_tag)

        # Create child tag that depends on parent
        child_data = {
            'type': 'tag',
            'name': 'child-tag',
            'parent': 'parent-tag'
        }
        child_tag = Tag(child_data)
        obj_map.add_object(child_tag)

        # Test dependency resolution
        dependents = child_tag.dependents(obj_map)
        assert len(dependents) == 1
        assert dependents[0].name == 'parent-tag'

    def test_dependents_with_missing_dependencies(self):
        """Test dependency resolution with missing dependencies."""

        obj_map = ObjectMap(OfflineResolver())

        # Create tag with missing parent
        data = {
            'type': 'tag',
            'name': 'orphan-tag',
            'parent': 'missing-parent'
        }
        tag = Tag(data)
        obj_map.add_object(tag)

        # Should not crash, but return empty list for missing deps
        dependents = tag.dependents(obj_map)
        assert len(dependents) == 0

    def test_koji_diff_stub(self):
        """Test that koji_diff returns empty list (stub implementation)."""

        data = {'type': 'user', 'name': 'testuser'}
        obj = User(data)

        # Should return empty list (stub)
        diff_result = obj.koji_diff(None)
        assert diff_result == []

        # Should also work with actual koji data
        koji_data = {'name': 'testuser', 'description': 'Existing user'}
        diff_result = obj.koji_diff(koji_data)
        assert diff_result == []


class TestUserModel:
    """Test User model functionality."""

    def test_user_creation(self):
        """Test creating a user object."""

        data = {
            'type': 'user',
            'name': 'testuser',
            'description': 'Test user account',
            'email': 'test@example.com'
        }

        user = User(data)

        assert user.type == 'user'
        assert user.name == 'testuser'
        assert user.data['email'] == 'test@example.com'

    def test_user_dependent_keys(self):
        """Test user dependency keys."""

        data = {'type': 'user', 'name': 'testuser'}
        user = User(data)

        # Users typically don't have dependencies
        deps = user.dependent_keys()
        assert deps == []

    def test_user_with_minimal_data(self):
        """Test user creation with minimal required data."""

        data = {'type': 'user', 'name': 'minimaluser'}
        user = User(data)

        assert user.name == 'minimaluser'
        assert user.data == data


class TestTagModel:
    """Test Tag model functionality."""

    def test_tag_creation(self):
        """Test creating a tag object."""

        data = {
            'type': 'tag',
            'name': 'test-tag',
            'description': 'Test build tag',
            'parent': 'parent-tag'
        }

        tag = Tag(data)

        assert tag.type == 'tag'
        assert tag.name == 'test-tag'
        assert tag.data['parent'] == 'parent-tag'

    def test_tag_dependent_keys(self):
        """Test tag dependency keys."""

        data = {
            'type': 'tag',
            'name': 'child-tag',
            'parent': 'parent-tag'
        }
        tag = Tag(data)

        deps = tag.dependent_keys()
        assert ('tag', 'parent-tag') in deps

    def test_tag_without_parent(self):
        """Test tag creation without parent."""

        data = {
            'type': 'tag',
            'name': 'root-tag',
            'description': 'Root build tag'
        }
        tag = Tag(data)

        deps = tag.dependent_keys()
        assert deps == []

    def test_tag_with_multiple_dependencies(self):
        """Test tag with multiple dependencies."""

        data = {
            'type': 'tag',
            'name': 'complex-tag',
            'parent': 'parent-tag',
            'inherit_from': ['inherit-tag1', 'inherit-tag2']
        }
        tag = Tag(data)

        deps = tag.dependent_keys()
        assert ('tag', 'parent-tag') in deps
        assert ('tag', 'inherit-tag1') in deps
        assert ('tag', 'inherit-tag2') in deps


class TestExternalRepoModel:
    """Test ExternalRepo model functionality."""

    def test_external_repo_creation(self):
        """Test creating an external repo object."""

        data = {
            'type': 'external-repo',
            'name': 'epel',
            'url': 'https://download.fedoraproject.org/pub/epel/',
            'tag': 'el9-build'
        }

        repo = ExternalRepo(data)

        assert repo.type == 'external-repo'
        assert repo.name == 'epel'
        assert repo.data['url'] == 'https://download.fedoraproject.org/pub/epel/'

    def test_external_repo_dependent_keys(self):
        """Test external repo dependency keys."""

        data = {
            'type': 'external-repo',
            'name': 'epel',
            'url': 'https://download.fedoraproject.org/pub/epel/',
            'tag': 'el9-build'
        }
        repo = ExternalRepo(data)

        deps = repo.dependent_keys()
        assert ('tag', 'el9-build') in deps


class TestTargetModel:
    """Test Target model functionality."""

    def test_target_creation(self):
        """Test creating a target object."""

        data = {
            'type': 'target',
            'name': 'el9-build',
            'build_tag': 'el9-build',
            'dest_tag': 'el9-candidate'
        }

        target = Target(data)

        assert target.type == 'target'
        assert target.name == 'el9-build'
        assert target.data['build_tag'] == 'el9-build'

    def test_target_dependent_keys(self):
        """Test target dependency keys."""

        data = {
            'type': 'target',
            'name': 'el9-build',
            'build_tag': 'el9-build',
            'dest_tag': 'el9-candidate'
        }
        target = Target(data)

        deps = target.dependent_keys()
        assert ('tag', 'el9-build') in deps
        assert ('tag', 'el9-candidate') in deps


class TestHostModel:
    """Test Host model functionality."""

    def test_host_creation(self):
        """Test creating a host object."""

        data = {
            'type': 'host',
            'name': 'build-host-01',
            'arches': ['x86_64', 'aarch64'],
            'capacity': 10.0
        }

        host = Host(data)

        assert host.type == 'host'
        assert host.name == 'build-host-01'
        assert host.data['arches'] == ['x86_64', 'aarch64']

    def test_host_dependent_keys(self):
        """Test host dependency keys."""

        data = {
            'type': 'host',
            'name': 'build-host-01',
            'arches': ['x86_64'],
            'capacity': 10.0
        }
        host = Host(data)

        # Hosts typically don't have dependencies
        deps = host.dependent_keys()
        assert deps == []


class TestGroupModel:
    """Test Group model functionality."""

    def test_group_creation(self):
        """Test creating a group object."""

        data = {
            'type': 'group',
            'name': 'build',
            'tag': 'el9-build',
            'packages': ['gcc', 'make', 'rpm-build']
        }

        group = Group(data)

        assert group.type == 'group'
        assert group.name == 'build'
        assert group.data['packages'] == ['gcc', 'make', 'rpm-build']

    def test_group_dependent_keys(self):
        """Test group dependency keys."""

        data = {
            'type': 'group',
            'name': 'build',
            'tag': 'el9-build',
            'packages': ['gcc', 'make']
        }
        group = Group(data)

        deps = group.dependent_keys()
        assert ('tag', 'el9-build') in deps


class TestModelDataIntegrity:
    """Test data integrity and validation across models."""

    def test_required_fields_preserved(self):
        """Test that required fields are preserved in all models."""

        for model_type, model_class in CORE_MODELS.items():
            data = {'type': model_type, 'name': f'test-{model_type}'}
            obj = model_class(data)

            # All objects should have type and name
            assert obj.type == model_type
            assert obj.name == f'test-{model_type}'
            assert obj.data['type'] == model_type
            assert obj.data['name'] == f'test-{model_type}'

    def test_data_copy_isolation(self):
        """Test that object data is isolated from original."""

        original_data = {
            'type': 'user',
            'name': 'testuser',
            'description': 'Original description'
        }

        user = User(original_data)

        # Modify original data
        original_data['description'] = 'Modified description'

        # Object data should be unchanged
        assert user.data['description'] == 'Original description'

    def test_dependent_keys_consistency(self):
        """Test that dependent_keys returns consistent results."""

        data = {
            'type': 'tag',
            'name': 'child-tag',
            'parent': 'parent-tag'
        }
        tag = Tag(data)

        # Should return same results multiple times
        deps1 = tag.dependent_keys()
        deps2 = tag.dependent_keys()
        assert deps1 == deps2

    def test_model_key_uniqueness(self):
        """Test that model keys are unique based on type and name."""

        data1 = {'type': 'user', 'name': 'testuser'}
        data2 = {'type': 'user', 'name': 'testuser'}
        data3 = {'type': 'tag', 'name': 'testuser'}  # Different type, same name

        user1 = User(data1)
        user2 = User(data2)
        tag = Tag(data3)

        # Same type and name should have same key
        assert user1.key == user2.key

        # Different type should have different key
        assert user1.key != tag.key


# The end.

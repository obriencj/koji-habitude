"""
koji-habitude - test_data_loading

Unit tests for YAML object data loading functionality.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

import pytest
import yaml
from pathlib import Path
from unittest.mock import Mock, patch

from koji_habitude.loader import (
    load_yaml_documents,
    resolve_object_type,
    create_core_object,
    expand_template_object,
    process_object_data,
    load_object_data,
    validate_object_data,
    get_object_summary,
    print_load_summary
)
from koji_habitude.object_map import ObjectMap, OfflineResolver
from koji_habitude.templates import Template


DATA_DIR = Path(__file__).parent / 'data'


class TestLoadYamlDocuments:
    """Test YAML document loading functionality."""


    def test_load_single_document(self):
        """Test loading a single YAML document."""

        data_file = DATA_DIR / 'single_document.yaml'

        docs = list(load_yaml_documents(data_file))

        assert len(docs) == 1
        assert docs[0]['type'] == 'user'
        assert docs[0]['name'] == 'testuser'
        assert docs[0]['description'] == 'Test user account'


    def test_load_multiple_documents(self):
        """Test loading multiple YAML documents from single file."""

        data_file = DATA_DIR / 'multiple_documents.yaml'

        docs = list(load_yaml_documents(data_file))

        assert len(docs) == 2
        assert docs[0]['name'] == 'user1'
        assert docs[1]['name'] == 'user2'


    def test_load_empty_documents(self):
        """Test handling of empty or null documents."""

        data_file = DATA_DIR / 'empty_documents.yaml'

        docs = list(load_yaml_documents(data_file))

        assert len(docs) == 2
        assert docs[0]['name'] == 'valid_user'
        assert docs[1]['name'] == 'valid_tag'


    def test_load_invalid_yaml(self):
        """Test handling of invalid YAML content."""

        data_file = DATA_DIR / 'bad' / 'invalid_yaml.yaml'

        docs = list(load_yaml_documents(data_file))

        # Should not raise exception, but return empty list
        assert len(docs) == 0


    def test_load_nonexistent_file(self):
        """Test handling of nonexistent file."""

        docs = list(load_yaml_documents(Path('/nonexistent/file.yaml')))
        assert len(docs) == 0


class TestResolveObjectType:
    """Test object type resolution functionality."""


    def test_resolve_core_type(self):
        """Test resolving core model types."""

        obj_data = {'type': 'user', 'name': 'testuser'}
        templates = {}

        obj_type = resolve_object_type(obj_data, templates)
        assert obj_type == 'user'


    def test_resolve_template_type(self):
        """Test resolving template types."""

        obj_data = {'type': 'custom_template', 'name': 'testobj'}
        templates = {'custom_template': Mock(spec=Template)}

        obj_type = resolve_object_type(obj_data, templates)
        assert obj_type == 'custom_template'


    def test_resolve_unknown_type(self):
        """Test handling of unknown object types."""

        obj_data = {'type': 'unknown_type', 'name': 'testobj'}
        templates = {}

        with pytest.raises(ValueError, match='Unknown object type'):
            resolve_object_type(obj_data, templates)


    def test_resolve_missing_type(self):
        """Test handling of missing type field."""

        obj_data = {'name': 'testobj'}
        templates = {}

        with pytest.raises(ValueError, match="Object missing 'type' field"):
            resolve_object_type(obj_data, templates)


class TestCreateCoreObject:
    """Test core object creation functionality."""


    def test_create_user_object(self):
        """Test creating a user object."""

        obj_data = {
            'type': 'user',
            'name': 'testuser',
            'description': 'Test user account'
        }

        obj = create_core_object(obj_data)
        assert obj.type == 'user'
        assert obj.name == 'testuser'
        assert obj.data['description'] == 'Test user account'


    def test_create_tag_object(self):
        """Test creating a tag object."""

        obj_data = {
            'type': 'tag',
            'name': 'test-tag',
            'description': 'Test tag'
        }

        obj = create_core_object(obj_data)
        assert obj.type == 'tag'
        assert obj.name == 'test-tag'


    def test_create_non_core_type(self):
        """Test handling of non-core object types."""

        obj_data = {'type': 'unknown_type', 'name': 'testobj'}

        with pytest.raises(ValueError, match="'unknown_type' is not a core model type"):
            create_core_object(obj_data)


class TestValidateObjectData:
    """Test object data validation functionality."""


    def test_validate_valid_data(self):
        """Test validation of valid object data."""

        obj_data = {'type': 'user', 'name': 'testuser'}
        assert validate_object_data(obj_data) is True


    def test_validate_missing_type(self):
        """Test validation of data missing type field."""

        obj_data = {'name': 'testuser'}
        assert validate_object_data(obj_data) is False


    def test_validate_missing_name(self):
        """Test validation of data missing name field."""

        obj_data = {'type': 'user'}
        assert validate_object_data(obj_data) is False


    def test_validate_missing_both_fields(self):
        """Test validation of data missing both required fields."""

        obj_data = {'description': 'Some description'}
        assert validate_object_data(obj_data) is False


class TestLoadObjectData:
    """Test object data loading from directory."""


    def test_load_from_directory(self):
        """Test loading objects from a directory."""

        data_dir = DATA_DIR / 'data_loading' / 'load_from_directory'

        # Load objects
        obj_map = ObjectMap(OfflineResolver())
        templates = {}

        load_object_data(str(data_dir), templates, obj_map)

        # Verify objects were loaded
        assert len(obj_map) == 4  # 2 users + 2 tags
        assert ('user', 'user1') in obj_map
        assert ('user', 'user2') in obj_map
        assert ('tag', 'tag1') in obj_map
        assert ('tag', 'tag2') in obj_map


    def test_load_from_nonexistent_directory(self):
        """Test loading from nonexistent directory."""

        obj_map = ObjectMap(OfflineResolver())
        templates = {}

        with pytest.raises(FileNotFoundError):
            load_object_data('/nonexistent/directory', templates, obj_map)


    def test_load_with_duplicate_objects(self):
        """Test handling of duplicate objects."""

        data_dir = DATA_DIR / 'data_loading' / 'load_with_duplicate_objects'

        obj_map = ObjectMap(OfflineResolver())
        templates = {}

        # Should not raise exception, but print warning
        with patch('builtins.print') as mock_print:
            load_object_data(str(data_dir), templates, obj_map)

            # Verify warning was printed
            mock_print.assert_any_call('Warning: Duplicate object (\'user\', \'duplicate_user\'), overriding')

        # Verify only one object exists (last one wins)
        assert len(obj_map) == 1
        assert obj_map.get_object(('user', 'duplicate_user')).data['description'] == 'Second instance (should override)'


    def test_load_with_invalid_objects(self):
        """Test handling of invalid objects."""

        data_dir = DATA_DIR / 'data_loading' / 'load_with_invalid_objects'

        obj_map = ObjectMap(OfflineResolver())
        templates = {}

        # Should not raise exception, but print error and continue
        with patch('builtins.print') as mock_print:
            load_object_data(str(data_dir), templates, obj_map)

            # Verify error was printed (check for the error message pattern)
            error_calls = [call for call in mock_print.call_args_list if 'Error processing object in' in str(call)]
            assert len(error_calls) > 0

        # Verify only valid object was loaded
        assert len(obj_map) == 1
        assert ('tag', 'valid_tag') in obj_map


class TestObjectSummary:
    """Test object summary functionality."""

    def test_get_object_summary(self):
        """Test getting summary of objects by type."""

        obj_map = ObjectMap(OfflineResolver())
        templates = {}

        # Add some test objects
        user1_data = {'type': 'user', 'name': 'user1'}
        user2_data = {'type': 'user', 'name': 'user2'}
        tag1_data = {'type': 'tag', 'name': 'tag1'}

        user1 = create_core_object(user1_data)
        user2 = create_core_object(user2_data)
        tag1 = create_core_object(tag1_data)

        obj_map.add_object(user1)
        obj_map.add_object(user2)
        obj_map.add_object(tag1)

        summary = get_object_summary(obj_map)

        assert summary['user'] == 2
        assert summary['tag'] == 1


    def test_print_load_summary(self):
        """Test printing load summary."""

        obj_map = ObjectMap(OfflineResolver())

        # Add test objects
        user_data = {'type': 'user', 'name': 'testuser'}
        tag_data = {'type': 'tag', 'name': 'testtag'}

        user_obj = create_core_object(user_data)
        tag_obj = create_core_object(tag_data)

        obj_map.add_object(user_obj)
        obj_map.add_object(tag_obj)


        with patch('builtins.print') as mock_print:
            print_load_summary(obj_map)

            # Verify summary was printed
            mock_print.assert_any_call('\nLoaded 2 objects:')
            mock_print.assert_any_call('  tag: 1')
            mock_print.assert_any_call('  user: 1')


class TestProcessObjectData:
    """Test object data processing functionality."""


    def test_process_core_object(self):
        """Test processing core object data."""

        obj_data = {'type': 'user', 'name': 'testuser'}
        templates = {}

        objects = process_object_data(obj_data, templates)

        assert len(objects) == 1
        assert objects[0].type == 'user'
        assert objects[0].name == 'testuser'


    def test_process_template_object(self):
        """Test processing template object data."""

        obj_data = {'type': 'custom_template', 'name': 'testobj', 'param1': 'value1'}

        # Mock template and its expansion
        mock_template = Mock(spec=Template)
        templates = {'custom_template': mock_template}

        # Mock the expand_template function to return core objects
        expanded_data = [
            {'type': 'user', 'name': 'expanded_user'},
            {'type': 'tag', 'name': 'expanded_tag'}
        ]

        with patch('koji_habitude.loader.expand_template', return_value=expanded_data):
            objects = process_object_data(obj_data, templates)

            assert len(objects) == 2
            assert objects[0].type == 'user'
            assert objects[0].name == 'expanded_user'
            assert objects[1].type == 'tag'
            assert objects[1].name == 'expanded_tag'


    def test_process_object_missing_name(self):
        """Test processing object data missing name field."""

        obj_data = {'type': 'user'}
        templates = {}

        with pytest.raises(ValueError, match="Object missing 'name' field"):
            process_object_data(obj_data, templates)


# The end.

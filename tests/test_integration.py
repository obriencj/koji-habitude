"""
koji-habitude - test_integration

Integration tests for loading data and templates together.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

import pytest
import yaml
from pathlib import Path
from unittest.mock import patch

from koji_habitude.loader import load_object_data
from koji_habitude.templates import load_templates
from koji_habitude.object_map import ObjectMap, OfflineResolver


DATA_DIR = Path(__file__).parent / 'data' / 'integration'


class TestDataTemplateIntegration:
    """Test integration between data loading and template expansion."""

    def test_load_data_with_templates(self):
        """Test loading data that uses templates."""

        base_dir = DATA_DIR / 'load_data_with_templates'
        templates_dir = base_dir / 'templates'
        data_dir = base_dir / 'data'

        # Load templates
        templates = load_templates(str(templates_dir))

        # Load data
        obj_map = ObjectMap(OfflineResolver())
        load_object_data(str(data_dir), templates, obj_map)

        # Verify objects were created
        # Should have 2 users + 2 tags from templates + 1 direct user = 5 total
        assert len(obj_map) == 5

        # Check template-expanded objects
        assert ('user', 'developer1') in obj_map
        assert ('tag', 'developer1-tag') in obj_map
        assert ('user', 'developer2') in obj_map
        assert ('tag', 'developer2-tag') in obj_map

        # Check direct object
        assert ('user', 'direct_user') in obj_map

        # Verify object data
        dev1_user = obj_map.get_object(('user', 'developer1'))
        assert dev1_user.data['description'] == 'Primary developer account'

        dev1_tag = obj_map.get_object(('tag', 'developer1-tag'))
        assert dev1_tag.data['description'] == 'Build tag for developer1'
        assert dev1_tag.data['parent'] == 'el9-build'

    def test_load_data_with_nested_templates(self):
        """Test loading data with templates that reference other templates."""

        base_dir = DATA_DIR / 'load_data_with_nested_templates'
        templates_dir = base_dir / 'templates'
        data_dir = base_dir / 'data'

        # Load templates and data
        templates = load_templates(str(templates_dir))
        obj_map = ObjectMap(OfflineResolver())
        load_object_data(str(data_dir), templates, obj_map)

        # Verify objects were created
        # Should have 1 user from base_user template + 1 user + 1 tag from developer template = 3 total
        assert len(obj_map) == 3

        # Check base user
        assert ('user', 'admin_user') in obj_map
        admin_user = obj_map.get_object(('user', 'admin_user'))
        assert admin_user.data['email'] == 'admin@example.com'

        # Check developer user and tag
        assert ('user', 'dev_user') in obj_map
        assert ('tag', 'dev_user-dev-tag') in obj_map

        dev_user = obj_map.get_object(('user', 'dev_user'))
        assert dev_user.data['email'] == 'dev@example.com'

        dev_tag = obj_map.get_object(('tag', 'dev_user-dev-tag'))
        assert dev_tag.data['parent'] == 'el9-build'

    def test_load_data_with_template_errors(self):
        """Test handling of template expansion errors."""

        base_dir = DATA_DIR / 'load_data_with_template_errors'
        templates_dir = base_dir / 'templates'
        data_dir = base_dir / 'data'

        # Load templates and data
        templates = load_templates(str(templates_dir))
        obj_map = ObjectMap(OfflineResolver())

        # Should not crash, but print error and continue
        with patch('builtins.print') as mock_print:
            load_object_data(str(data_dir), templates, obj_map)

            # Verify error was printed (check for the error message pattern)
            error_calls = [call for call in mock_print.call_args_list if 'Error processing object in' in str(call)]
            assert len(error_calls) > 0

        # Should have only the working user
        assert len(obj_map) == 1
        assert ('user', 'working_user') in obj_map

    def test_load_data_with_mixed_content(self):
        """Test loading data with mixed core objects and templates."""

        base_dir = DATA_DIR / 'load_data_with_mixed_content'
        templates_dir = base_dir / 'templates'
        data_dir = base_dir / 'data'

        # Load templates and data
        templates = load_templates(str(templates_dir))
        obj_map = ObjectMap(OfflineResolver())
        load_object_data(str(data_dir), templates, obj_map)

        # Verify all objects were created
        assert len(obj_map) == 3

        # Check template-generated user
        assert ('user', 'templated_user') in obj_map
        templated_user = obj_map.get_object(('user', 'templated_user'))
        assert templated_user.data['description'] == 'User from template'

        # Check direct objects
        assert ('tag', 'direct_tag') in obj_map
        assert ('user', 'direct_user') in obj_map

        direct_tag = obj_map.get_object(('tag', 'direct_tag'))
        assert direct_tag.data['parent'] == 'el9-build'

        direct_user = obj_map.get_object(('user', 'direct_user'))
        assert direct_user.data['email'] == 'user@example.com'

    def test_load_data_with_multiple_files(self):
        """Test loading data from multiple files with templates."""

        base_dir = DATA_DIR / 'load_data_with_multiple_files'
        templates_dir = base_dir / 'templates'
        data_dir = base_dir / 'data'

        # Load templates and data
        templates = load_templates(str(templates_dir))
        obj_map = ObjectMap(OfflineResolver())
        load_object_data(str(data_dir), templates, obj_map)

        # Verify all objects were loaded
        assert len(obj_map) == 4

        # Check users from template
        assert ('user', 'user1') in obj_map
        assert ('user', 'user2') in obj_map

        # Check direct tags
        assert ('tag', 'tag1') in obj_map
        assert ('tag', 'tag2') in obj_map

        # Verify relationships
        tag2 = obj_map.get_object(('tag', 'tag2'))
        assert tag2.data['parent'] == 'tag1'

    def test_load_data_with_template_validation_failure(self):
        """Test handling of template validation failures."""

        base_dir = DATA_DIR / 'load_data_with_template_validation_failure'
        templates_dir = base_dir / 'templates'
        data_dir = base_dir / 'data'

        # Load templates and data
        templates = load_templates(str(templates_dir))
        obj_map = ObjectMap(OfflineResolver())

        # Should handle validation gracefully (currently always passes)
        with patch('builtins.print') as mock_print:
            load_object_data(str(data_dir), templates, obj_map)

        # All objects should be loaded (validation is currently not enforced)
        assert len(obj_map) == 3
        assert ('user', 'valid_user') in obj_map
        assert ('user', 'invalid_user') in obj_map
        assert ('user', 'direct_user') in obj_map

    def test_load_data_with_complex_template_structure(self):
        """Test loading data with complex template that generates multiple objects."""

        base_dir = DATA_DIR / 'load_data_with_complex_template_structure'
        templates_dir = base_dir / 'templates'
        data_dir = base_dir / 'data'

        # Load templates and data
        templates = load_templates(str(templates_dir))
        obj_map = ObjectMap(OfflineResolver())
        load_object_data(str(data_dir), templates, obj_map)

        # Verify all objects were created (2 developers * 4 objects each = 8 total)
        assert len(obj_map) == 8

        # Check Alice's objects
        assert ('user', 'alice') in obj_map
        assert ('tag', 'alice-dev') in obj_map
        assert ('tag', 'alice-test') in obj_map
        assert ('external-repo', 'alice-repo') in obj_map

        # Check Bob's objects
        assert ('user', 'bob') in obj_map
        assert ('tag', 'bob-dev') in obj_map
        assert ('tag', 'bob-test') in obj_map
        assert ('external-repo', 'bob-repo') in obj_map

        # Verify relationships
        alice_dev_tag = obj_map.get_object(('tag', 'alice-dev'))
        assert alice_dev_tag.data['parent'] == 'el9-build'

        alice_test_tag = obj_map.get_object(('tag', 'alice-test'))
        assert alice_test_tag.data['parent'] == 'alice-dev'

        alice_repo = obj_map.get_object(('external-repo', 'alice-repo'))
        assert alice_repo.data['tag'] == 'alice-dev'
        assert alice_repo.data['url'] == 'https://repos.example.com/alice'


# The end.

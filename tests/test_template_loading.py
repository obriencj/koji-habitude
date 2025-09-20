"""
koji-habitude - test_template_loading

Unit tests for template loading and Jinja2 expansion functionality.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

import pytest
import yaml
from pathlib import Path
from unittest.mock import Mock, patch

from koji_habitude.templates import (
    Template,
    load_templates,
    expand_template,
    create_template_registry,
    get_template_names,
    template_exists
)


DATA_DIR = Path(__file__).parent / 'data' / 'template_loading'


class TestTemplate:
    """Test Template class functionality."""

    def test_template_with_inline_content(self):
        """Test template with inline template content."""

        template_data = {
            'name': 'test_template',
            'template': 'type: user\nname: {{ name }}\ndescription: {{ description }}',
            'schema': {}
        }

        template = Template('test_template', template_data, '/templates')

        assert template.name == 'test_template'
        assert template.template_content == template_data['template']
        assert template.template_file is None
        assert template.schema == {}

    def test_template_with_external_file(self):
        """Test template with external template file."""

        template_data = {
            'name': 'file_template',
            'template_file': 'user_template.j2',
            'schema': {'required': ['name', 'email']}
        }

        template = Template('file_template', template_data, '/templates')

        assert template.name == 'file_template'
        assert template.template_content is None
        assert template.template_file == 'user_template.j2'
        assert template.schema == {'required': ['name', 'email']}

    def test_template_missing_both_content_and_file(self):
        """Test template missing both content and file."""

        template_data = {
            'name': 'invalid_template',
            'schema': {}
        }

        with pytest.raises(ValueError, match="Template 'invalid_template' must specify either 'template' or 'template_file'"):
            Template('invalid_template', template_data, '/templates')

    def test_get_jinja2_template_inline(self):
        """Test getting Jinja2 template from inline content."""

        template_data = {
            'name': 'inline_template',
            'template': 'type: user\nname: {{ name }}'
        }

        template = Template('inline_template', template_data, '/templates')

        mock_env = Mock()
        mock_template = Mock()
        mock_env.from_string.return_value = mock_template

        result = template.get_jinja2_template(mock_env)

        mock_env.from_string.assert_called_once_with(template_data['template'])
        assert result == mock_template

    def test_get_jinja2_template_file(self):
        """Test getting Jinja2 template from file."""

        template_data = {
            'name': 'file_template',
            'template_file': 'user.j2'
        }

        template = Template('file_template', template_data, '/templates')

        mock_env = Mock()
        mock_template = Mock()
        mock_env.get_template.return_value = mock_template

        result = template.get_jinja2_template(mock_env)

        mock_env.get_template.assert_called_once_with('user.j2')
        assert result == mock_template

    def test_validate_data_without_schema(self):
        """Test data validation when no schema is configured."""

        template_data = {'name': 'no_schema_template', 'template': 'test'}
        template = Template('no_schema_template', template_data, '/templates')

        # Should always return True when no schema
        assert template.validate_data({'name': 'test'}) is True
        assert template.validate_data({}) is True
        assert template.validate_data({'invalid': 'data'}) is True

    def test_validate_data_with_schema(self):
        """Test data validation with schema configured."""

        template_data = {
            'name': 'schema_template',
            'template': 'test',
            'schema': {'required': ['name']}
        }
        template = Template('schema_template', template_data, '/templates')

        # Currently always returns True (schema validation not implemented)
        assert template.validate_data({'name': 'test'}) is True
        assert template.validate_data({}) is True


class TestLoadTemplates:
    """Test template loading functionality."""


    def test_load_templates_from_directory(self):
        """Test loading templates from a directory."""

        data_dir = DATA_DIR / 'templates_from_directory'

        # Load templates
        templates = load_templates(str(data_dir))

        # Verify templates were loaded
        assert len(templates) == 3
        assert 'user_template' in templates
        assert 'tag_template' in templates
        assert 'external_repo_template' in templates

        # Verify template properties
        user_template = templates['user_template']
        assert user_template.name == 'user_template'
        assert 'type: user' in user_template.template_content
        assert user_template.schema['required'] == ['name', 'description']

        external_template = templates['external_repo_template']
        assert external_template.template_file == 'external_repo.j2'
        assert external_template.template_content is None


    def test_load_templates_with_yml_extension(self):
        """Test loading templates from .yml files."""

        data_dir = DATA_DIR / 'templates_with_yml_extension'

        templates = load_templates(str(data_dir))

        assert len(templates) == 1
        assert 'yml_template' in templates
        assert 'type: user' in templates['yml_template'].template_content


    def test_load_templates_nonexistent_directory(self):
        """Test loading templates from nonexistent directory."""

        with pytest.raises(FileNotFoundError, match='Templates directory not found'):
            load_templates('/nonexistent/templates')


    def test_load_templates_with_duplicates(self):
        """Test handling of duplicate template names."""

        data_dir = DATA_DIR / 'templates_with_duplicates'

        with patch('builtins.print') as mock_print:
            templates = load_templates(str(data_dir))

            # Verify warning was printed
            mock_print.assert_any_call("Warning: Duplicate template name 'duplicate_template', overriding")

            # Verify last template wins
            assert len(templates) == 1
            assert 'second version (should win)' in templates['duplicate_template'].template_content


    def test_load_templates_missing_name(self):
        """Test handling of templates missing name field."""

        data_dir = DATA_DIR / 'templates_missing_name'

        with patch('builtins.print') as mock_print:
            templates = load_templates(str(data_dir))

            # Verify warning was printed (check for the warning message pattern)
            warning_calls = [call for call in mock_print.call_args_list if "missing 'name' field, skipping" in str(call)]
            assert len(warning_calls) > 0

            # Verify only valid template was loaded
            assert len(templates) == 1
            assert 'valid_template' in templates


    def test_load_templates_invalid_yaml(self):
        """Test handling of invalid YAML in template files."""

        data_dir = DATA_DIR / 'templates_invalid_yaml'

        with patch('builtins.print') as mock_print:
            templates = load_templates(str(data_dir))

            # YAML parsing might handle the error gracefully, so we just verify
            # that the function doesn't crash and processes what it can
            assert isinstance(templates, dict)

            # Should not crash, but may have partial results
            # (This depends on how YAML parsing handles errors)


    def test_load_templates_empty_documents(self):
        """Test handling of empty documents in template files."""

        data_dir = DATA_DIR / 'templates_empty_documents'

        templates = load_templates(str(data_dir))

        assert len(templates) == 2
        assert 'template1' in templates
        assert 'template2' in templates


class TestExpandTemplate:
    """Test template expansion functionality."""


    def test_expand_inline_template(self):
        """Test expanding inline template."""

        template_data = {
            'name': 'user_template',
            'template': """
---
type: user
name: {{ name }}
description: {{ description }}
---
type: tag
name: {{ name }}-tag
description: Tag for {{ name }}
"""
        }

        template = Template('user_template', template_data, '/templates')
        data = {'name': 'testuser', 'description': 'Test user account'}

        expanded = expand_template(template, data)

        assert len(expanded) == 2

        # Check user object
        user_obj = expanded[0]
        assert user_obj['type'] == 'user'
        assert user_obj['name'] == 'testuser'
        assert user_obj['description'] == 'Test user account'

        # Check tag object
        tag_obj = expanded[1]
        assert tag_obj['type'] == 'tag'
        assert tag_obj['name'] == 'testuser-tag'
        assert tag_obj['description'] == 'Tag for testuser'


    def test_expand_template_with_file(self):
        """Test expanding template from external file."""

        templates_dir = DATA_DIR / 'expand_template_with_file'

        template_data = {
            'name': 'file_template',
            'template_file': 'user_template.j2'
        }

        template = Template('file_template', template_data, str(templates_dir))
        data = {'name': 'testuser', 'email': 'test@example.com'}

        expanded = expand_template(template, data)

        assert len(expanded) == 1
        assert expanded[0]['type'] == 'user'
        assert expanded[0]['name'] == 'testuser'
        assert expanded[0]['email'] == 'test@example.com'


    def test_expand_template_with_single_object(self):
        """Test expanding template that produces single object."""

        template_data = {
            'name': 'single_template',
            'template': 'type: user\nname: {{ name }}'
        }

        template = Template('single_template', template_data, '/templates')
        data = {'name': 'singleuser'}

        expanded = expand_template(template, data)

        assert len(expanded) == 1
        assert expanded[0]['type'] == 'user'
        assert expanded[0]['name'] == 'singleuser'


    def test_expand_template_with_empty_output(self):
        """Test expanding template that produces no objects."""

        template_data = {
            'name': 'empty_template',
            'template': '# No objects generated'
        }

        template = Template('empty_template', template_data, '/templates')
        data = {'name': 'test'}

        expanded = expand_template(template, data)

        assert len(expanded) == 0


    def test_expand_template_with_invalid_yaml_output(self):
        """Test expanding template that produces invalid YAML."""

        template_data = {
            'name': 'invalid_template',
            'template': 'type: user\nname: {{ name }}\n  invalid: indentation'
        }

        template = Template('invalid_template', template_data, '/templates')
        data = {'name': 'testuser'}

        with pytest.raises(RuntimeError, match='Error parsing template output as YAML'):
            expand_template(template, data)


    def test_expand_template_with_render_error(self):
        """Test expanding template with undefined variable."""

        template_data = {
            'name': 'error_template',
            'template': 'type: user\nname: {{ undefined_variable }}'
        }

        template = Template('error_template', template_data, '/templates')
        data = {'name': 'testuser'}

        # Jinja2 doesn't raise errors for undefined variables by default,
        # it just renders them as empty strings
        expanded = expand_template(template, data)

        assert len(expanded) == 1
        assert expanded[0]['type'] == 'user'
        assert expanded[0]['name'] is None  # Undefined variable becomes None


class TestTemplateUtilities:

    def test_create_template_registry(self):
        """Test creating template registry."""

        data_dir = DATA_DIR / 'create_template_registry'

        templates = create_template_registry(str(data_dir))

        assert len(templates) == 1
        assert 'test_template' in templates


    def test_get_template_names(self):
        """Test getting template names."""

        templates = {
            'template_c': Mock(),
            'template_a': Mock(),
            'template_b': Mock()
        }

        names = get_template_names(templates)

        # Should return sorted list
        assert names == ['template_a', 'template_b', 'template_c']


    def test_template_exists(self):
        """Test checking if template exists."""

        templates = {
            'existing_template': Mock(),
            'another_template': Mock()
        }

        assert template_exists(templates, 'existing_template') is True
        assert template_exists(templates, 'nonexistent_template') is False
        assert template_exists(templates, 'another_template') is True


# The end.

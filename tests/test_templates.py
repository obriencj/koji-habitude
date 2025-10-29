"""
koji-habitude - test_templates

Unit tests for koji_habitude.templates module.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated


from pathlib import Path
import unittest
from unittest.mock import mock_open, patch

from pydantic import ValidationError

from koji_habitude.loader import MultiLoader, YAMLLoader
from koji_habitude.templates import (
    Template,
    TemplateCall,
    TemplateModelDefinition,
    TemplateFieldDefinition,
    ValidationRule,
)


def load_documents_from_paths(paths):
    """
    Helper function to load YAML documents from file paths using MultiLoader.

    :param paths: List of file or directory paths to load from
    :returns: List of loaded YAML documents with metadata
    """

    multiloader = MultiLoader([YAMLLoader])
    return list(multiloader.load(paths))


def find_template_documents(documents):
    """
    Helper function to find template documents from a list of loaded documents.

    :param documents: List of loaded YAML documents
    :returns: List of documents where type == 'template'
    """

    return [doc for doc in documents if doc.get('type') == 'template']


class TestTemplateCall(unittest.TestCase):
    """
    Test cases for the TemplateCall class.
    """

    def test_template_call_initialization(self):
        """
        Test TemplateCall initialization with valid data.
        """

        data = {
            'type': 'my-template',
            'name': 'test-object',
            'property': 'value'
        }
        call = TemplateCall.from_dict(data)

        self.assertEqual(call.template_name, 'my-template', "Should extract typename from data")
        self.assertEqual(call.data, data, "Should store original data")

    def test_template_call_with_metadata(self):
        """
        Test TemplateCall initialization with loader metadata.
        """

        data = {
            'type': 'complex-template',
            'name': 'test-object',
            '__file__': '/path/to/file.yaml',
            '__line__': 42
        }
        call = TemplateCall.from_dict(data)

        self.assertEqual(call.template_name, 'complex-template')
        self.assertEqual(call.data['__file__'], '/path/to/file.yaml')
        self.assertEqual(call.data['__line__'], 42)


class TestTemplate(unittest.TestCase):
    """
    Test cases for the Template class.
    """

    def setUp(self):
        """
        Set up test data paths.
        """

        self.test_data_dir = Path(__file__).parent / 'data'
        self.templates_dir = self.test_data_dir / 'templates'
        self.bad_dir = self.test_data_dir / 'bad'

    def test_template_initialization_with_inline_content(self):
        """
        Test Template initialization with inline content.
        """

        template_data = {
            'type': 'template',
            'name': 'test-template',
            'content': '---\ntype: tag\nname: {{ name }}\n',
        }
        template = Template.from_dict(template_data)

        self.assertEqual(template.name, 'test-template')
        self.assertEqual(template.template_content, template_data['content'])
        self.assertIsNone(template.template_file)
        self.assertIsNotNone(template.jinja2_template)


    def test_template_name_validation(self):
        """
        Test template name validation requirements.
        """

        # Test empty name
        with self.assertRaises(ValidationError) as context:
            Template(type='template', content='test content')
        self.assertIn("field required", str(context.exception).lower())

        # Test None name
        with self.assertRaises(ValidationError) as context:
            Template(type='template', name=None, content='test content')
        self.assertIn("name is required for template", str(context.exception))

        # Test whitespace-only name (should not be accepted by pydantic)
        with self.assertRaises(ValueError) as context:
            Template(type='template', name='   ', content='test content')
        self.assertIn("name is required for template", str(context.exception))


    def test_template_content_validation(self):
        """
        Test template content validation requirements.
        """

        # Test missing both content and file
        from koji_habitude.exceptions import TemplateError
        with self.assertRaises(TemplateError) as context:
            Template(type='template', name='test-template')
        self.assertIn("Template content is required", str(context.exception))

        # Test both content and file specified
        from koji_habitude.exceptions import TemplateError
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_dir', return_value=True):
            with self.assertRaises(TemplateError) as context:
                Template(
                    type='template',
                    name='test-template',
                    content='test content',
                    file='template.j2',
                    __file__='/fake/path'
                )
            self.assertIn("Template content is not allowed when template file is specified",
                          str(context.exception))


    def test_template_file_path_validation(self):
        """
        Test template file path validation.
        """

        # Test missing base path when file is specified
        from koji_habitude.exceptions import TemplateError
        with self.assertRaises(TemplateError) as context:
            Template(
                type='template',
                name='test-template',
                file='template.j2'
            )
        self.assertIn("'template.j2' not found in search path:", str(context.exception))

        # Test non-existent base path
        from koji_habitude.exceptions import TemplateError
        with patch('pathlib.Path.exists', return_value=False):
            with self.assertRaises(TemplateError) as context:
                Template(
                    type='template',
                    name='test-template',
                    file='template.j2',
                    __file__='/nonexistent/path'
                )
            self.assertIn("'template.j2' not found in search path:", str(context.exception))

        # Test base path is not a directory
        from koji_habitude.exceptions import TemplateError
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.is_dir', return_value=False):
            with self.assertRaises(TemplateError) as context:
                Template(
                    type='template',
                    name='test-template',
                    file='template.j2',
                    __file__='/path/to/file.txt'
                )
            self.assertIn("'template.j2' not found in search path:", str(context.exception))

    def test_template_repr(self):
        """
        Test Template string representation.
        """

        template_data = {
            'type': 'template',
            'name': 'test-template',
            'content': 'test content',
        }
        template = Template.from_dict(template_data)

        repr_str = repr(template)
        self.assertEqual('<Template(test-template)>', repr_str)

    def test_render_simple_template(self):
        """
        Test basic template rendering with Jinja2.
        """

        template_data = {
            'type': 'template',
            'name': 'greeting-template',
            'content': 'Hello {{ name }}!',
        }
        template = Template.from_dict(template_data)

        result = template.render({'name': 'World'})
        self.assertEqual(result, 'Hello World!')

    def test_render_yaml_template(self):
        """
        Test rendering a YAML template.
        """

        template_data = {
            'type': 'template',
            'name': 'tag-template',
            'content': '''---
type: tag
name: {{ name }}
arches:
{% for arch in arches %}
  - {{ arch }}
{% endfor %}''',
        }
        template = Template.from_dict(template_data)

        data = {
            'name': 'test-tag',
            'arches': ['x86_64', 'aarch64']
        }
        result = template.render(data)

        self.assertIn('name: test-tag', result)
        self.assertIn('- x86_64', result)
        self.assertIn('- aarch64', result)

    def test_render_and_load_basic(self):
        """
        Test render_and_load with basic YAML output.
        """

        template_data = {
            'type': 'template',
            'name': 'tag-template',
            'content': '''---
type: tag
name: {{ name }}''',
        }
        template = Template.from_dict(template_data)

        # Set tracing attributes that would normally be set by namespace
        template.filename = '/path/to/template.yaml'
        template.lineno = 1

        data = {
            'name': 'test-tag',
        }

        results = list(template.render_and_load(data))
        self.assertEqual(len(results), 1)

        result = results[0]
        self.assertEqual(result['type'], 'tag')
        self.assertEqual(result['name'], 'test-tag')

    def test_render_and_load_multiple_documents(self):
        """
        Test render_and_load with multiple YAML documents.
        """

        template_data = {
            'type': 'template',
            'name': 'multi-template',
            'content': '''---
type: tag
name: {{ name }}-build
---
type: tag
name: {{ name }}-dest'''
        }
        template = Template.from_dict(template_data)

        # Set tracing attributes that would normally be set by namespace
        template.filename = '/path/to/template.yaml'
        template.lineno = 1

        data = {'name': 'fedora-39'}

        results = list(template.render_and_load(data))
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0]['name'], 'fedora-39-build')
        self.assertEqual(results[1]['name'], 'fedora-39-dest')

    def test_render_and_load_tracing_system(self):
        """
        Test the tracing system in render_and_load.
        """

        template_data = {
            'type': 'template',
            'name': 'trace-template',
            'content': '''---
type: tag
name: {{ name }}'''
        }
        template = Template.from_dict(template_data)

        # Mock the filename and lineno properties that would be set by namespace
        template.filename = '/path/to/template.yaml'
        template.lineno = 5

        data = {
            'name': 'test-tag',
            '__file__': '/path/to/data.yaml',
            '__line__': 10
        }

        results = list(template.render_and_load(data))
        result = results[0]

        # Check tracing information was added
        self.assertIn('__trace__', result)
        self.assertIn('__file__', result)
        self.assertIn('__line__', result)

        self.assertEqual(result['__file__'], '/path/to/data.yaml')
        self.assertEqual(result['__line__'], 10)

        trace = result['__trace__']
        self.assertIsInstance(trace, list)
        self.assertEqual(len(trace), 1)

        trace_entry = trace[0]
        self.assertEqual(trace_entry['name'], 'trace-template')
        self.assertEqual(trace_entry['file'], '/path/to/template.yaml')
        self.assertEqual(trace_entry['line'], 5)

    def test_render_and_load_nested_tracing(self):
        """
        Test tracing system with existing trace information.
        """

        template_data = {
            'type': 'template',
            'name': 'nested-template',
            'content': '''---
type: tag
name: {{ name }}'''
        }
        template = Template.from_dict(template_data)

        template.filename = '/path/to/nested.yaml'
        template.lineno = 8

        existing_trace = [{
            'name': 'parent-template',
            'file': '/path/to/parent.yaml',
            'line': 3
        }]

        data = {
            'name': 'nested-tag',
            '__trace__': existing_trace,
            '__file__': '/path/to/data.yaml',
            '__line__': 15
        }

        results = list(template.render_and_load(data))
        result = results[0]

        trace = result['__trace__']
        self.assertEqual(len(trace), 2)

        # Original trace entry should be preserved
        self.assertEqual(trace[0]['name'], 'parent-template')

        # New trace entry should be appended
        self.assertEqual(trace[1]['name'], 'nested-template')
        self.assertEqual(trace[1]['file'], '/path/to/nested.yaml')
        self.assertEqual(trace[1]['line'], 8)

    def test_render_call_method(self):
        """
        Test the render_call convenience method.
        """

        template_data = {
            'type': 'template',
            'name': 'call-template',
            'content': '''---
type: tag
name: {{ name }}'''
        }
        template = Template.from_dict(template_data)

        # Set tracing attributes that would normally be set by namespace
        template.filename = '/path/to/template.yaml'
        template.lineno = 1

        call_data = {
            'type': 'call-template',
            'name': 'test-tag'
        }
        call = TemplateCall.from_dict(call_data)

        results = list(template.render_call(call))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'test-tag')


    def test_jinja2_error_propagation(self):
        """
        Test that Jinja2 template errors are propagated, not caught.
        """

        # Template with malformed Jinja2 syntax
        # Template creation should fail with malformed Jinja2 syntax
        from koji_habitude.exceptions import TemplateSyntaxError
        with self.assertRaises(TemplateSyntaxError):
            Template(
                type='template',
                name='bad-jinja-template',
                content='''---
type: tag
name: {{ name }
# Missing closing brace'''
            )

    def test_jinja2_filter_error_propagation(self):
        """
        Test that Jinja2 filter errors are propagated, not caught.
        """

        # Template with an invalid filter (error at template creation time)
        # Template creation should fail with invalid filter
        from jinja2.exceptions import TemplateAssertionError
        with self.assertRaises(TemplateAssertionError):
            Template(
                type='template',
                name='filter-error-template',
                content='''---
type: tag
name: {{ name }}
description: "{{ name | invalid_filter }}"'''
            )


    def test_template_with_real_test_data(self):
        """
        Test template creation using real test data files.
        """

        # Load a template from our test data
        inline_template_path = self.templates_dir / 'inline_content.yaml'

        # We'll simulate what the loader would do
        import yaml
        with open(inline_template_path, 'r') as f:
            docs = list(yaml.safe_load_all(f))

        template_doc = docs[0]  # Should be the template document
        self.assertEqual(template_doc['type'], 'template')
        self.assertEqual(template_doc['name'], 'inline-tag-template')

        # Create template from the loaded data
        template = Template.from_dict(template_doc)
        template.filename = str(inline_template_path)
        template.lineno = 2  # Line where template starts

        # Test rendering with data
        data = {
            'name': 'fedora-39-build',
            'arches': ['x86_64', 'aarch64'],
            'parents': ['fedora-39-base']
        }

        results = list(template.render_and_load(data))
        self.assertEqual(len(results), 1)

        result = results[0]
        self.assertEqual(result['type'], 'tag')
        self.assertEqual(result['name'], 'fedora-39-build')
        self.assertIn('x86_64', result['arches'])
        self.assertIn('aarch64', result['arches'])
        self.assertEqual(len(result['inheritance']), 1)
        self.assertEqual(result['inheritance'][0]['name'], 'fedora-39-base')
        self.assertEqual(result['inheritance'][0]['priority'], 10)

    def test_external_template_file_with_real_data(self):
        """
        Test external template file using real test data.
        """

        # Use the actual template directory for this test
        template_data = {
            'type': 'template',
            'name': 'external-target-template',
            'file': 'target_template.j2',
            '__file__': str(self.templates_dir / 'fake.yml'),
            '__line__': 2,
        }

        template = Template.from_dict(template_data)

        data = {
            'name': 'fedora-39',
            'build_tag': 'fedora-39-build',
        }

        results = list(template.render_and_load(data))
        self.assertEqual(len(results), 1)

        result = results[0]
        self.assertEqual(result['type'], 'target')
        self.assertEqual(result['name'], 'fedora-39')
        self.assertEqual(result['build-tag'], 'fedora-39-build')
        self.assertEqual(result['dest-tag'], 'fedora-39-dest')


class TestTemplatesWithRealFiles(unittest.TestCase):
    """
    Test cases using real YAML and .j2 files loaded via MultiLoader.
    """

    def setUp(self):
        """
        Set up test data paths.
        """

        self.test_data_dir = Path(__file__).parent / 'data'
        self.templates_dir = self.test_data_dir / 'templates'

    def test_load_inline_template_with_multiloader(self):
        """
        Test loading and using an inline template via MultiLoader.
        """

        # Load the inline content template file
        template_file = self.templates_dir / 'inline_content.yaml'
        documents = load_documents_from_paths([template_file])

        # Should find one document
        self.assertEqual(len(documents), 1)

        # Find template documents
        template_docs = find_template_documents(documents)
        self.assertEqual(len(template_docs), 1)

        template_doc = template_docs[0]
        self.assertEqual(template_doc['name'], 'inline-tag-template')
        self.assertEqual(template_doc['type'], 'template')
        self.assertIn('content', template_doc)

        # Create template from document
        template = Template.from_dict(template_doc)

        # Verify template properties
        self.assertEqual(template.name, 'inline-tag-template')
        self.assertIsNotNone(template.template_content)
        self.assertIsNone(template.template_file)
        self.assertEqual(template.filename, str(template_file))
        self.assertEqual(template.lineno, 3)  # Line where template starts in YAML

        # Test rendering
        data = {
            'name': 'test-build-tag',
            'description': 'Test build tag',
            'arches': ['x86_64', 'aarch64'],
            'parents': ['base-tag', 'updates-tag'],
        }

        results = list(template.render_and_load(data))
        self.assertEqual(len(results), 1)

        result = results[0]
        self.assertEqual(result['type'], 'tag')
        self.assertEqual(result['name'], 'test-build-tag')
        self.assertEqual(result['arches'], ['x86_64', 'aarch64'])

        # Check inheritance was properly rendered
        self.assertIn('inheritance', result)
        print(result['inheritance'])
        self.assertEqual(len(result['inheritance']), 2)
        self.assertEqual(result['inheritance'][0]['name'], 'base-tag')
        self.assertEqual(result['inheritance'][0]['priority'], 10)
        self.assertEqual(result['inheritance'][1]['name'], 'updates-tag')
        self.assertEqual(result['inheritance'][1]['priority'], 20)

    def test_load_external_template_with_multiloader(self):
        """
        Test loading and using an external template file via MultiLoader.
        """

        # Load the external file template
        template_file = self.templates_dir / 'external_file.yaml'
        documents = load_documents_from_paths([template_file])

        # Should find one document
        self.assertEqual(len(documents), 1)

        template_doc = documents[0]
        self.assertEqual(template_doc['name'], 'external-target-template')
        self.assertEqual(template_doc['type'], 'template')
        self.assertEqual(template_doc['file'], 'target_template.j2')
        self.assertNotIn('content', template_doc)

        # Create template from document
        template = Template.from_dict(template_doc)

        # Verify template properties
        self.assertEqual(template.name, 'external-target-template')
        self.assertEqual(template.template_file, 'target_template.j2')
        self.assertIsNone(template.template_content)
        self.assertEqual(template.base_path, self.templates_dir)

        # Test rendering
        data = {
            'name': 'fedora-39',
            'build_tag': 'fedora-39-build',
            'dest_tag': 'fedora-39-candidate',
        }

        results = list(template.render_and_load(data))
        self.assertEqual(len(results), 1)

        result = results[0]
        self.assertEqual(result['type'], 'target')
        self.assertEqual(result['name'], 'fedora-39')
        self.assertEqual(result['build-tag'], 'fedora-39-build')
        self.assertEqual(result['dest-tag'], 'fedora-39-candidate')

        # Verify tracing information
        self.assertIn('__trace__', result)
        trace = result['__trace__'][0]
        self.assertEqual(trace['name'], 'external-target-template')
        self.assertEqual(trace['file'], str(template_file))

    def test_load_external_template_without_dest_tag(self):
        """
        Test external template with optional fields (conditional Jinja2).
        """

        template_file = self.templates_dir / 'external_file.yaml'
        documents = load_documents_from_paths([template_file])
        template = Template.from_dict(documents[0])

        data = {
            'name': 'minimal-target',
            'build_tag': 'minimal-build',
        }

        results = list(template.render_and_load(data))
        result = results[0]

        self.assertEqual(result['type'], 'target')
        self.assertEqual(result['name'], 'minimal-target')
        self.assertEqual(result['build-tag'], 'minimal-build')
        self.assertEqual(result['dest-tag'], 'minimal-target-dest')

    def test_load_multi_output_template_with_multiloader(self):
        """
        Test loading and using a template that generates multiple documents.
        """

        template_file = self.templates_dir / 'multi_output.yaml'
        documents = load_documents_from_paths([template_file])

        template_doc = documents[0]
        self.assertEqual(template_doc['name'], 'multi-output-template')

        template = Template.from_dict(template_doc)

        # Test rendering - should generate 3 documents
        data = {
            'name': 'fedora-40',
            'arches': ['x86_64', 'aarch64', 's390x']
        }

        results = list(template.render_and_load(data))
        self.assertEqual(len(results), 3)

        # Check build tag
        build_tag = results[0]
        self.assertEqual(build_tag['type'], 'tag')
        self.assertEqual(build_tag['name'], 'fedora-40-build')
        self.assertEqual(build_tag['arches'], ['x86_64', 'aarch64', 's390x'])

        # Check dest tag
        dest_tag = results[1]
        self.assertEqual(dest_tag['type'], 'tag')
        self.assertEqual(dest_tag['name'], 'fedora-40-dest')
        self.assertIn('inheritance', dest_tag)
        self.assertEqual(dest_tag['inheritance'][0]['name'], 'fedora-40-build')

        # Check target
        target = results[2]
        self.assertEqual(target['type'], 'target')
        self.assertEqual(target['name'], 'fedora-40')
        self.assertEqual(target['build-tag'], 'fedora-40-build')
        self.assertEqual(target['dest-tag'], 'fedora-40-dest')

    def test_load_all_templates_from_directory(self):
        """
        Test loading all template files from the templates directory.
        """

        # Load all documents from templates directory
        documents = load_documents_from_paths([self.templates_dir])

        # Find all template documents
        template_docs = find_template_documents(documents)

        # We should find at least our known templates
        template_names = {doc['name'] for doc in template_docs}
        expected_names = {
            'inline-tag-template',
            'external-target-template',
            'multi-output-template'
        }

        self.assertTrue(expected_names.issubset(template_names),
                       f"Missing templates: {expected_names - template_names}")

        # Test that we can create Template objects from all of them that have content or file
        for template_doc in template_docs:
            # Skip templates that don't have content or file (like the old test templates)
            if 'content' in template_doc or 'file' in template_doc:
                template = Template.from_dict(template_doc)
                self.assertIsInstance(template, Template)
                self.assertEqual(template.name, template_doc['name'])

    def test_template_tracing_with_real_files(self):
        """
        Test that tracing information is properly preserved with real files.
        """

        template_file = self.templates_dir / 'inline_content.yaml'
        documents = load_documents_from_paths([template_file])
        template = Template.from_dict(documents[0])

        # Create data with existing trace information (simulating nested expansion)
        data = {
            'name': 'traced-tag',
            'arches': ['x86_64'],
            'parents':  [],
            '__file__': '/path/to/data.yaml',
            '__line__': 42,
            '__trace__': [{
                'name': 'parent-template',
                'file': '/path/to/parent.yaml',
                'line': 10
            }]
        }

        results = list(template.render_and_load(data))
        result = results[0]

        # Check that original metadata is preserved
        self.assertEqual(result['__file__'], '/path/to/data.yaml')
        self.assertEqual(result['__line__'], 42)

        # Check that trace chain is maintained
        trace = result['__trace__']
        self.assertEqual(len(trace), 2)

        # Original trace entry
        self.assertEqual(trace[0]['name'], 'parent-template')
        self.assertEqual(trace[0]['file'], '/path/to/parent.yaml')
        self.assertEqual(trace[0]['line'], 10)

        # New trace entry
        self.assertEqual(trace[1]['name'], 'inline-tag-template')
        self.assertEqual(trace[1]['file'], str(template_file))
        self.assertEqual(trace[1]['line'], 3)


class TestTemplateDynamicModels(unittest.TestCase):
    """
    Test cases for dynamic model feature in templates.
    """

    def test_basic_model_creation_string_field(self):
        """
        Test creating a model with a simple string field.
        """

        model_def = TemplateModelDefinition(
            name="TestModel",
            fields={
                "name": TemplateFieldDefinition(type="string")
            }
        )

        self.assertIsNotNone(model_def._model_class)
        self.assertEqual(model_def._model_class.__name__, "TestModel")

        # Test creating an instance
        instance = model_def.new({"name": "test-value"})
        self.assertEqual(instance.name, "test-value")

    def test_basic_model_creation_multiple_field_types(self):
        """
        Test creating a model with multiple basic field types.
        """

        model_def = TemplateModelDefinition(
            name="MultiTypeModel",
            fields={
                "name": TemplateFieldDefinition(type="string"),
                "count": TemplateFieldDefinition(type="int"),
                "price": TemplateFieldDefinition(type="float"),
                "active": TemplateFieldDefinition(type="bool")
            }
        )

        instance = model_def.new({
            "name": "product",
            "count": 42,
            "price": 19.99,
            "active": True
        })

        self.assertEqual(instance.name, "product")
        self.assertEqual(instance.count, 42)
        self.assertEqual(instance.price, 19.99)
        self.assertEqual(instance.active, True)

    def test_optional_field_with_default(self):
        """
        Test creating a model with optional fields and defaults.
        """

        model_def = TemplateModelDefinition(
            name="OptionalModel",
            fields={
                "required_field": TemplateFieldDefinition(
                    type="string",
                    required=True
                ),
                "optional_field": TemplateFieldDefinition(
                    type="string",
                    required=False
                ),
                "default_field": TemplateFieldDefinition(
                    type="string",
                    default="default-value"
                )
            }
        )

        # Test with minimal data
        instance1 = model_def.new({"required_field": "value"})
        self.assertEqual(instance1.required_field, "value")
        self.assertIsNone(instance1.optional_field)
        self.assertEqual(instance1.default_field, "default-value")

        # Test with all fields provided
        instance2 = model_def.new({
            "required_field": "value",
            "optional_field": "optional",
            "default_field": "custom"
        })
        self.assertEqual(instance2.optional_field, "optional")
        self.assertEqual(instance2.default_field, "custom")

    def test_field_with_alias(self):
        """
        Test creating a model with field aliases.
        """

        model_def = TemplateModelDefinition(
            name="AliasModel",
            fields={
                "display_name": TemplateFieldDefinition(
                    type="string",
                    alias="name"
                )
            }
        )

        # Should accept both the field name and alias
        instance = model_def.new({"name": "aliased-value"})
        self.assertEqual(instance.display_name, "aliased-value")

    def test_string_validation_min_max_length(self):
        """
        Test string field validation with min/max length.
        """

        model_def = TemplateModelDefinition(
            name="ValidatedStringModel",
            fields={
                "code": TemplateFieldDefinition(
                    type="string",
                    validation=ValidationRule(
                        min_length=3,
                        max_length=10
                    )
                )
            }
        )

        # Valid cases
        instance1 = model_def.new({"code": "abc"})
        self.assertEqual(instance1.code, "abc")

        instance2 = model_def.new({"code": "1234567890"})
        self.assertEqual(instance2.code, "1234567890")

        # Invalid cases
        with self.assertRaises(ValidationError):
            model_def.new({"code": "ab"})  # Too short

        with self.assertRaises(ValidationError):
            model_def.new({"code": "12345678901"})  # Too long

    def test_int_validation_min_max_value(self):
        """
        Test integer field validation with min/max value.
        """

        model_def = TemplateModelDefinition(
            name="ValidatedIntModel",
            fields={
                "score": TemplateFieldDefinition(
                    type="int",
                    validation=ValidationRule(
                        min_value=0,
                        max_value=100
                    )
                )
            }
        )

        # Valid cases
        instance1 = model_def.new({"score": 0})
        self.assertEqual(instance1.score, 0)

        instance2 = model_def.new({"score": 100})
        self.assertEqual(instance2.score, 100)

        instance3 = model_def.new({"score": 50})
        self.assertEqual(instance3.score, 50)

        # Invalid cases - should raise ValidationError
        # BUG: These currently don't raise ValidationError. The min_value and max_value
        # validation rules are passed to Field() but Pydantic Field() doesn't accept
        # these as keyword arguments. The validation rules need to be handled differently,
        # possibly using Pydantic validators or constraints.
        with self.assertRaises(ValidationError):
            model_def.new({"score": -1})  # Below min_value=0

        with self.assertRaises(ValidationError):
            model_def.new({"score": 101})  # Above max_value=100

    def test_string_validation_pattern(self):
        """
        Test string field validation with regex pattern.
        """

        model_def = TemplateModelDefinition(
            name="PatternModel",
            fields={
                "email": TemplateFieldDefinition(
                    type="string",
                    validation=ValidationRule(
                        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                    )
                )
            }
        )

        # Valid case
        instance = model_def.new({"email": "test@example.com"})
        self.assertEqual(instance.email, "test@example.com")

        # Invalid case
        with self.assertRaises(ValidationError):
            model_def.new({"email": "not-an-email"})

    def test_enum_validation(self):
        """
        Test enum field validation.
        """

        model_def = TemplateModelDefinition(
            name="EnumModel",
            fields={
                "status": TemplateFieldDefinition(
                    type="enum",
                    validation=ValidationRule(
                        enum_values=["pending", "active", "completed"]
                    )
                )
            }
        )

        # Valid cases
        # Note: enum values are returned as Enum instances, need to access the value
        instance1 = model_def.new({"status": "pending"})
        self.assertEqual(instance1.status.value, "pending")

        instance2 = model_def.new({"status": "active"})
        self.assertEqual(instance2.status.value, "active")

        # Invalid case
        with self.assertRaises(ValidationError):
            model_def.new({"status": "invalid"})

    def test_array_field_type(self):
        """
        Test array field type.
        """

        model_def = TemplateModelDefinition(
            name="ArrayModel",
            fields={
                "items": TemplateFieldDefinition(type="array")
            }
        )

        instance = model_def.new({"items": [1, 2, 3, "four"]})
        self.assertEqual(instance.items, [1, 2, 3, "four"])

    def test_typed_array_field(self):
        """
        Test array field with typed items.
        """

        model_def = TemplateModelDefinition(
            name="TypedArrayModel",
            fields={
                "numbers": TemplateFieldDefinition(
                    type="array",
                    array_item_type=TemplateFieldDefinition(type="int")
                )
            }
        )

        instance = model_def.new({"numbers": [1, 2, 3, 4, 5]})
        self.assertEqual(instance.numbers, [1, 2, 3, 4, 5])

    def test_object_field_type(self):
        """
        Test object field type with nested fields.
        """

        model_def = TemplateModelDefinition(
            name="ObjectModel",
            fields={
                "metadata": TemplateFieldDefinition(
                    type="object",
                    object_fields={
                        "author": TemplateFieldDefinition(type="string"),
                        "version": TemplateFieldDefinition(type="int")
                    },
                    object_type_name="Metadata"
                )
            }
        )

        instance = model_def.new({
            "metadata": {
                "author": "test-author",
                "version": 1
            }
        })

        self.assertEqual(instance.metadata.author, "test-author")
        self.assertEqual(instance.metadata.version, 1)

    def test_template_with_model_validation_success(self):
        """
        Test template rendering with model validation - success case.
        """

        template = Template.from_dict({
            "name": "validated-template",
            "content": "name: {{ TestModel.name }}\ncount: {{ TestModel.count }}",
            "model": {
                "name": "TestModel",
                "fields": {
                    "name": {"type": "string"},
                    "count": {"type": "int"}
                }
            }
        })

        data = {"name": "test-name", "count": 42}
        result = template.render(data)

        self.assertIn("name: test-name", result)
        self.assertIn("count: 42", result)

    def test_template_with_model_validation_failure(self):
        """
        Test template rendering with model validation - failure case.
        """

        template = Template.from_dict({
            "name": "validated-template",
            "content": "name: {{ TestModel.name }}",
            "model": {
                "name": "TestModel",
                "fields": {
                    "name": {
                        "type": "string",
                        "validation": {
                            "min_length": 3
                        }
                    }
                }
            }
        })

        # Invalid data - name too short
        with self.assertRaises(ValidationError):
            template.render({"name": "ab"})

    def test_template_model_instance_accessible(self):
        """
        Test that model instance is accessible in template with correct name.
        """

        template = Template.from_dict({
            "name": "model-access-template",
            "content": "{{ TestModel.name }}-{{ TestModel.count }}",
            "model": {
                "name": "TestModel",
                "fields": {
                    "name": {"type": "string"},
                    "count": {"type": "int"}
                }
            }
        })

        data = {"name": "test", "count": 5}
        result = template.render(data)

        self.assertEqual(result.strip(), "test-5")

    def test_template_original_data_preserved(self):
        """
        Test that original data is still accessible as _data in template.
        """

        template = Template.from_dict({
            "name": "data-preservation-template",
            "content": "model: {{ TestModel.value }}\ndata: {{ _data.value }}",
            "model": {
                "name": "TestModel",
                "fields": {
                    "value": {"type": "string"}
                }
            }
        })

        data = {"value": "test-value", "extra": "extra-value"}
        result = template.render(data)

        self.assertIn("model: test-value", result)
        self.assertIn("data: test-value", result)

    def test_template_model_with_defaults(self):
        """
        Test that template defaults merge with call data before validation.
        """

        template = Template.from_dict({
            "name": "defaults-template",
            "defaults": {
                "optional": "default-optional"
            },
            "content": "required: {{ TestModel.required }}\noptional: {{ TestModel.optional }}",
            "model": {
                "name": "TestModel",
                "fields": {
                    "required": {"type": "string"},
                    "optional": {"type": "string", "required": False}
                }
            }
        })

        # Provide only required field, optional should come from defaults
        data = {"required": "test-required"}
        result = template.render(data)

        self.assertIn("required: test-required", result)
        self.assertIn("optional: default-optional", result)

    def test_template_complex_nested_access(self):
        """
        Test template accessing nested model properties.
        """

        template = Template.from_dict({
            "name": "nested-template",
            "content": "author: {{ TestModel.config.author }}\nversion: {{ TestModel.config.version }}",
            "model": {
                "name": "TestModel",
                "fields": {
                    "config": {
                        "type": "object",
                        "object_fields": {
                            "author": {"type": "string"},
                            "version": {"type": "int"}
                        },
                        "object_type_name": "Config"
                    }
                }
            }
        })

        data = {
            "config": {
                "author": "test-author",
                "version": 2
            }
        }
        result = template.render(data)

        self.assertIn("author: test-author", result)
        self.assertIn("version: 2", result)

    def test_template_load_from_yaml_with_model(self):
        """
        Test loading a template with model definition from YAML structure.
        """

        template_data = {
            "name": "yaml-model-template",
            "content": "{{ ItemModel.name }}: {{ ItemModel.count }}",
            "model": {
                "name": "ItemModel",
                "fields": {
                    "name": {"type": "string"},
                    "count": {"type": "int"}
                }
            }
        }

        template = Template.from_dict(template_data)
        self.assertIsNotNone(template.template_model)
        self.assertEqual(template.template_model.name, "ItemModel")

        result = template.render({"name": "widget", "count": 10})
        self.assertIn("widget: 10", result)

    def test_template_mixed_field_types_validation(self):
        """
        Test template with multiple different field types all validated together.
        """

        template = Template.from_dict({
            "name": "mixed-types-template",
            "content": "{{ MixedModel.name }}-{{ MixedModel.count }}-{{ MixedModel.active }}",
            "model": {
                "name": "MixedModel",
                "fields": {
                    "name": {
                        "type": "string",
                        "validation": {"min-length": 1, "max-length": 10}
                    },
                    "count": {
                        "type": "int",
                        "validation": {"min-value": 0, "max-value": 100}
                    },
                    "active": {"type": "bool"}
                }
            }
        })

        # Valid data
        result = template.render({
            "name": "test",
            "count": 50,
            "active": True
        })
        self.assertIn("test-50-True", result)

        # Invalid string
        with self.assertRaises(ValidationError):
            template.render({
                "name": "too-long-string-value",
                "count": 50,
                "active": True
            })

        # Invalid int - should raise ValidationError
        # BUG: Same bug as above - min_value/max_value validation doesn't work for int fields
        with self.assertRaises(ValidationError):
            template.render({
                "name": "test",
                "count": 150,  # Above max_value=100
                "active": True
            })

    def test_template_enum_validation_in_context(self):
        """
        Test enum validation works correctly in template context.
        """

        template = Template.from_dict({
            "name": "enum-template",
            "content": "status: {{ StatusModel.status }}",
            "model": {
                "name": "StatusModel",
                "fields": {
                    "status": {
                        "type": "enum",
                        "validation": {
                            "enum_values": ["new", "in-progress", "done"]
                        }
                    }
                }
            }
        })

        # Valid enum value
        result = template.render({"status": "in-progress"})
        # Enum values render as their string representation
        self.assertIn("status:", result)
        # Check that the enum value is present (may be rendered differently)
        self.assertTrue("in-progress" in result or "Enum_" in result)

        # Invalid enum value
        with self.assertRaises(ValidationError):
            template.render({"status": "invalid-status"})

    def test_template_pattern_validation_in_context(self):
        """
        Test pattern validation works correctly in template context.
        """

        template = Template.from_dict({
            "name": "pattern-template",
            "content": "code: {{ CodeModel.code }}",
            "model": {
                "name": "CodeModel",
                "fields": {
                    "code": {
                        "type": "string",
                        "validation": {
                            "pattern": "^[A-Z]{3}-[0-9]{3}$"
                        }
                    }
                }
            }
        })

        # Valid pattern
        result = template.render({"code": "ABC-123"})
        self.assertIn("code: ABC-123", result)

        # Invalid pattern
        with self.assertRaises(ValidationError):
            template.render({"code": "invalid"})

    def test_validate_call_method(self):
        """
        Test the validate_call method on Template.
        """

        template = Template.from_dict({
            "name": "validation-template",
            "content": "test",
            "model": {
                "name": "TestModel",
                "fields": {
                    "value": {
                        "type": "string",
                        "validation": {"min_length": 3}
                    }
                }
            }
        })

        # Invalid call - should raise ValidationError
        with self.assertRaises(ValidationError):
            template.validate_call({"value": "ab"})

        # Valid call - should return True, not raise
        # BUG: validate_call currently raises ValidationError even for valid data.
        # It calls model_validate() on the TemplateModelDefinition instead of creating
        # a model instance. It should use model.new(data) instead.
        result = template.validate_call({"value": "valid"})
        self.assertTrue(result)  # Should return True for valid data, not raise

    def test_template_with_model_render_and_load(self):
        """
        Test that render_and_load works correctly with models.
        """

        template = Template.from_dict({
            "name": "model-render-load-template",
            "content": "---\ntype: tag\nname: {{ TagModel.name }}\narches: {{ TagModel.arches | join(', ') }}",
            "model": {
                "name": "TagModel",
                "fields": {
                    "name": {"type": "string"},
                    "arches": {
                        "type": "array",
                        "array_item_type": {"type": "string"}
                    }
                }
            }
        })

        data = {
            "name": "test-tag",
            "arches": ["x86_64", "aarch64"]
        }

        results = list(template.render_and_load(data))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["type"], "tag")
        self.assertEqual(results[0]["name"], "test-tag")
        self.assertEqual(results[0]["arches"], "x86_64, aarch64")


# The end.

"""
koji-habitude - test_expansion

Unit tests for namespace template expansion functionality including basic expansion,
deferred resolution, meta-template generation, and error handling.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated

from pathlib import Path
from unittest import TestCase

from jinja2.exceptions import TemplateSyntaxError
from pydantic import ValidationError

from koji_habitude.loader import YAMLLoader
from koji_habitude.models import Group, Tag, Target
from koji_habitude.namespace import ExpansionError, Namespace


def load_yaml_file(file_path):
    """
    Load YAML documents from a file using the koji_habitude YAMLLoader.

    Args:
        file_path: Path to the YAML file to load

    Returns:
        Iterator of documents from the YAML file
    """

    return YAMLLoader(file_path).load()


class TestBasicTemplateExpansion(TestCase):
    """Test cases for basic template expansion creating multiple objects."""

    def setUp(self):
        """Set up test fixtures."""

        self.ns = Namespace()
        self.test_data_dir = Path(__file__).parent / 'data' / 'namespace'


    def test_basic_product_expansion(self):
        """Test basic template that expands to multiple koji objects."""

        # Load test data
        documents = load_yaml_file(self.test_data_dir / 'test_basic_product_expansion.yaml')

        # Feed all documents and expand
        self.ns.feedall_raw(documents)
        self.ns.expand()

        # Verify template was processed and removed from feedline
        self.assertEqual(len(self.ns._feedline), 0)

        # Verify template is in template storage
        self.assertIn('product-template', self.ns._templates)

        # Verify expanded objects are in namespace storage
        expected_objects = [
            ('tag', 'myapp-build'),
            ('tag', 'myapp-dest'),
            ('target', 'myapp-target'),
            ('group', 'myapp-users'),
        ]

        for obj_type, obj_name in expected_objects:
            key = (obj_type, obj_name)
            self.assertIn(key, self.ns._ns, f"Missing {obj_type} {obj_name}")

        # Verify object types
        self.assertIsInstance(self.ns._ns[('tag', 'myapp-build')], Tag)
        self.assertIsInstance(self.ns._ns[('tag', 'myapp-dest')], Tag)
        self.assertIsInstance(self.ns._ns[('target', 'myapp-target')], Target)
        self.assertIsInstance(self.ns._ns[('group', 'myapp-users')], Group)

    def test_conditional_template_expansion(self):
        """Test template with conditional logic for optional components."""

        # Load test data with conditional template
        documents = load_yaml_file(self.test_data_dir / 'test_conditional_template_expansion.yaml')

        # Feed and expand
        self.ns.feedall_raw(documents)
        self.ns.expand()

        # Verify base objects exist
        self.assertIn(('tag', 'webapp-build'), self.ns._ns)
        self.assertIn(('tag', 'webapp-dest'), self.ns._ns)

        # Verify conditional override tag was created
        self.assertIn(('tag', 'webapp-override'), self.ns._ns)

        # Verify build tag has proper inheritance including override
        build_tag = self.ns._ns[('tag', 'webapp-build')]
        inheritance = build_tag.inheritance

        # Should have inheritance from both base and override
        parent_names = [p.name for p in inheritance]
        self.assertIn('webapp-dest', parent_names)
        self.assertIn('webapp-override', parent_names)

    def test_multiple_template_calls(self):
        """Test multiple calls to the same template with different parameters."""

        documents = load_yaml_file(self.test_data_dir / 'test_multiple_template_calls.yaml')

        self.ns.feedall_raw(documents)
        self.ns.expand()

        # Verify objects for both products exist
        products = ['frontend', 'backend']
        for product in products:
            expected_keys = [
                ('tag', f'{product}-build'),
                ('tag', f'{product}-dest'),
                ('target', f'{product}-target'),
                ('group', f'{product}-users')
            ]

            for key in expected_keys:
                self.assertIn(key, self.ns._ns, f"Missing {key[0]} {key[1]}")


class TestDeferredResolution(TestCase):
    """Test cases for deferred template resolution (templates used before definition)."""

    def setUp(self):
        """Set up test fixtures."""

        self.ns = Namespace()
        self.test_data_dir = Path(__file__).parent / 'data' / 'namespace'


    def test_template_used_before_definition(self):
        """Test template call appears before template definition in YAML."""

        documents = load_yaml_file(self.test_data_dir / 'test_deferred_template_resolution.yaml')

        # Feed all documents (template call comes before definition)
        self.ns.feedall_raw(documents)

        # Initially should have deferred objects in feedline
        self.assertGreater(len(self.ns._feedline), 0)

        # Expand should resolve the deferred template call
        self.ns.expand()

        # Verify expansion completed
        self.assertEqual(len(self.ns._feedline), 0)

        # Verify final objects exist
        self.assertIn(('tag', 'deferred-build'), self.ns._ns)
        self.assertIn(('tag', 'deferred-dest'), self.ns._ns)
        self.assertIn(('target', 'deferred-target'), self.ns._ns)

    def test_multi_stage_deferred_resolution(self):
        """Test complex deferred resolution with multiple dependency stages."""

        documents = load_yaml_file(self.test_data_dir / 'test_multi_stage_deferred.yaml')

        self.ns.feedall_raw(documents)
        self.ns.expand()

        # Verify all stages resolved correctly
        expected_objects = [
            ('tag', 'stage1-build'),
            ('tag', 'stage2-build'),
            ('tag', 'stage3-build'),
            ('target', 'final-target')
        ]

        for obj_type, obj_name in expected_objects:
            self.assertIn((obj_type, obj_name), self.ns._ns)


class TestMetaTemplateGeneration(TestCase):
    """Test cases for meta-templates that generate other templates."""

    def setUp(self):
        """Set up test fixtures."""

        self.ns = Namespace()
        self.test_data_dir = Path(__file__).parent / 'data' / 'namespace'


    def test_basic_meta_template_generation(self):
        """Test meta-template that generates another template."""

        documents = load_yaml_file(self.test_data_dir / 'test_basic_meta_template.yaml')

        self.ns.feedall_raw(documents)
        self.ns.expand()

        # Verify meta-template exists
        self.assertIn('gen-product', self.ns._templates)

        # Verify generated template exists with expected name
        self.assertIn('create-myapp-version', self.ns._templates)

        # Verify final objects from generated template exist
        expected_objects = [
            ('tag', 'myapp-1.0-build'),
            ('tag', 'myapp-1.0-dest'),
            ('target', 'myapp-1.0-target'),
            ('group', 'myapp-1.0-users')
        ]

        for obj_type, obj_name in expected_objects:
            self.assertIn((obj_type, obj_name), self.ns._ns)

    def test_conditional_meta_template(self):
        """Test meta-template with conditional logic in generated template."""

        documents = load_yaml_file(self.test_data_dir / 'test_conditional_meta_template.yaml')

        self.ns.feedall_raw(documents)
        self.ns.expand()

        # Verify generated template created conditional objects
        self.assertIn(('tag', 'webapp-2.0-build'), self.ns._ns)
        self.assertIn(('tag', 'webapp-2.0-override'), self.ns._ns)

        # Verify build tag uses override in inheritance
        build_tag = self.ns._ns[('tag', 'webapp-2.0-build')]
        inheritance = build_tag.inheritance
        parent_names = [p.name for p in inheritance]
        self.assertIn('webapp-2.0-override', parent_names)

    def test_nested_meta_template_generation(self):
        """Test meta-template that generates another meta-template."""

        documents = load_yaml_file(self.test_data_dir / 'test_nested_meta_template.yaml')

        self.ns.feedall_raw(documents)
        self.ns.expand()

        # Verify nested template generation chain
        self.assertIn('gen-product-family', self.ns._templates)  # Original meta-template
        self.assertIn('gen-myapp-product', self.ns._templates)   # Generated meta-template
        self.assertIn('create-myapp-frontend', self.ns._templates)  # Final generated template

        # Verify final objects exist
        self.assertIn(('tag', 'myapp-frontend-3.0-build'), self.ns._ns)
        self.assertIn(('target', 'myapp-frontend-3.0-target'), self.ns._ns)


class TestExpansionErrorHandling(TestCase):
    """Test cases for expansion error handling and deadlock detection."""

    def setUp(self):
        """Set up test fixtures."""

        self.ns = Namespace()
        self.test_data_dir = Path(__file__).parent / 'data' / 'namespace'


    def test_missing_template_deadlock(self):
        """Test deadlock detection when template is never defined."""

        documents = load_yaml_file(self.test_data_dir / 'test_missing_template_deadlock.yaml')

        self.ns.feedall_raw(documents)

        # Should raise ExpansionError indicating template resolution failure
        with self.assertRaises(ExpansionError) as context:
            self.ns.expand()

        self.assertIn("Could not resolve template", str(context.exception))
        self.assertIn("missing-template", str(context.exception))

    def test_circular_template_dependency(self):
        """Test detection of circular template dependencies."""

        documents = load_yaml_file(self.test_data_dir / 'test_circular_template_dependency.yaml')

        self.ns.feedall_raw(documents)

        # Should detect circular dependency and raise error
        with self.assertRaises(ExpansionError) as context:
            self.ns.expand()

        self.assertIn("Maximum depth", str(context.exception))

    def test_invalid_jinja2_syntax_error(self):
        """Test handling of invalid Jinja2 syntax in templates."""

        documents = load_yaml_file(self.test_data_dir / 'test_invalid_jinja2_syntax.yaml')

        # Should raise TemplateSyntaxError during template creation
        from koji_habitude.exceptions import TemplateSyntaxError
        with self.assertRaises(TemplateSyntaxError):
            self.ns.feedall_raw(documents)

    def test_meta_template_generates_invalid_template(self):
        """Test error when meta-template generates invalid template content."""

        documents = load_yaml_file(self.test_data_dir / 'test_invalid_generated_template.yaml')

        self.ns.feedall_raw(documents)

        # Should fail during expansion when trying to use generated template
        from koji_habitude.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.ns.expand()


# The end.

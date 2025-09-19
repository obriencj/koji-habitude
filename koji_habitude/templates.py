"""
koji-habitude - templates

Template loading and Jinja2 expansion system for koji object templates.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

import os
import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template as Jinja2Template


class Template:
    """
    Represents a koji object template.
    """
    
    def __init__(self, name: str, template_data: Dict[str, Any], templates_path: str):
        """
        Initialize template.
        
        Args:
            name: Name of the template
            template_data: Template configuration data
            templates_path: Path to templates directory
        """
        
        self.name = name
        self.data = template_data
        self.templates_path = templates_path
        
        # Template can specify inline content or external file
        self.template_content = template_data.get('template')
        self.template_file = template_data.get('template_file')
        self.schema = template_data.get('schema')
        
        if not self.template_content and not self.template_file:
            raise ValueError(f"Template '{name}' must specify either 'template' or 'template_file'")
            
    def get_jinja2_template(self, jinja_env: Environment) -> Jinja2Template:
        """
        Get Jinja2 template object.
        
        Args:
            jinja_env: Jinja2 environment to use
            
        Returns:
            Jinja2 template object
        """
        
        if self.template_content:
            return jinja_env.from_string(self.template_content)
        else:
            return jinja_env.get_template(self.template_file)
            
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate data against template schema if configured.
        
        Args:
            data: Data to validate
            
        Returns:
            True if validation passes or no schema configured
        """
        
        if not self.schema:
            return True
            
        # TODO: Implement schema validation
        # For now, just return True
        return True


def load_templates(templates_path: str) -> Dict[str, Template]:
    """
    Load all YAML templates from directory.
    
    Args:
        templates_path: Path to directory containing template files
        
    Returns:
        Dictionary mapping template names to Template objects
    """
    
    templates = {}
    templates_dir = Path(templates_path)
    
    if not templates_dir.exists():
        raise FileNotFoundError(f"Templates directory not found: {templates_path}")
        
    # Load all YAML files in the templates directory
    for yaml_file in templates_dir.glob("*.yaml"):
        try:
            with open(yaml_file, 'r') as f:
                template_docs = yaml.safe_load_all(f)
                
                for doc in template_docs:
                    if not doc:
                        continue
                        
                    template_name = doc.get('name')
                    if not template_name:
                        print(f"Warning: Template in {yaml_file} missing 'name' field, skipping")
                        continue
                        
                    if template_name in templates:
                        print(f"Warning: Duplicate template name '{template_name}', overriding")
                        
                    templates[template_name] = Template(template_name, doc, templates_path)
                    
        except yaml.YAMLError as e:
            print(f"Error loading template file {yaml_file}: {e}")
        except Exception as e:
            print(f"Error processing template file {yaml_file}: {e}")
            
    # Also check for .yml files
    for yaml_file in templates_dir.glob("*.yml"):
        try:
            with open(yaml_file, 'r') as f:
                template_docs = yaml.safe_load_all(f)
                
                for doc in template_docs:
                    if not doc:
                        continue
                        
                    template_name = doc.get('name')
                    if not template_name:
                        print(f"Warning: Template in {yaml_file} missing 'name' field, skipping")
                        continue
                        
                    if template_name in templates:
                        print(f"Warning: Duplicate template name '{template_name}', overriding")
                        
                    templates[template_name] = Template(template_name, doc, templates_path)
                    
        except yaml.YAMLError as e:
            print(f"Error loading template file {yaml_file}: {e}")
        except Exception as e:
            print(f"Error processing template file {yaml_file}: {e}")
            
    return templates


def expand_template(template: Template, data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Expand template using Jinja2 and return core objects.
    
    Args:
        template: Template to expand
        data: Data to use as template environment
        
    Returns:
        List of expanded object dictionaries
    """
    
    # Validate data against template schema
    if not template.validate_data(data):
        raise ValueError(f"Data validation failed for template '{template.name}'")
        
    # Set up Jinja2 environment
    if template.template_file:
        # Use file system loader for external templates
        jinja_env = Environment(
            loader=FileSystemLoader(template.templates_path),
            trim_blocks=True,
            lstrip_blocks=True
        )
    else:
        # Use basic environment for inline templates
        jinja_env = Environment(
            trim_blocks=True,
            lstrip_blocks=True
        )
        
    # Get the Jinja2 template
    jinja_template = template.get_jinja2_template(jinja_env)
    
    # Render the template
    try:
        rendered = jinja_template.render(**data)
    except Exception as e:
        raise RuntimeError(f"Error rendering template '{template.name}': {e}")
        
    # Parse the rendered output as YAML
    try:
        expanded_docs = list(yaml.safe_load_all(rendered))
        
        # Filter out None documents
        objects = [doc for doc in expanded_docs if doc is not None]
        
        return objects
        
    except yaml.YAMLError as e:
        raise RuntimeError(f"Error parsing template output as YAML for '{template.name}': {e}")


def create_template_registry(templates_path: str) -> Dict[str, Template]:
    """
    Create a template registry from the templates directory.
    
    Args:
        templates_path: Path to directory containing template files
        
    Returns:
        Dictionary mapping template names to Template objects
    """
    
    return load_templates(templates_path)


def get_template_names(templates: Dict[str, Template]) -> List[str]:
    """
    Get list of available template names.
    
    Args:
        templates: Dictionary of templates
        
    Returns:
        Sorted list of template names
    """
    
    return sorted(templates.keys())


def template_exists(templates: Dict[str, Template], name: str) -> bool:
    """
    Check if a template exists in the registry.
    
    Args:
        templates: Dictionary of templates
        name: Template name to check
        
    Returns:
        True if template exists
    """
    
    return name in templates

# The end.
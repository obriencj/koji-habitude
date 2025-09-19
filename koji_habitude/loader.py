"""
koji-habitude - loader

YAML object data loading functionality with template expansion.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

import yaml
from typing import Dict, List, Any, Iterator
from pathlib import Path

from .models import CORE_MODELS
from .models.base import BaseKojiObject
from .templates import Template, expand_template
from .object_map import ObjectMap


def load_yaml_documents(file_path: Path) -> Iterator[Dict[str, Any]]:
    """
    Load YAML documents from a file.
    
    Args:
        file_path: Path to YAML file
        
    Yields:
        Dictionary objects from the YAML file
    """
    
    try:
        with open(file_path, 'r') as f:
            docs = yaml.safe_load_all(f)
            for doc in docs:
                if doc is not None:
                    yield doc
    except yaml.YAMLError as e:
        print(f"Error loading YAML from {file_path}: {e}")
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")


def resolve_object_type(obj_data: Dict[str, Any], templates: Dict[str, Template]) -> str:
    """
    Resolve the type of an object (core model or template).
    
    Args:
        obj_data: Object data dictionary
        templates: Available templates
        
    Returns:
        Resolved type name
        
    Raises:
        ValueError: If type is not found in core models or templates
    """
    
    obj_type = obj_data.get('type')
    if not obj_type:
        raise ValueError("Object missing 'type' field")
        
    # Check if it's a core model type
    if obj_type in CORE_MODELS:
        return obj_type
        
    # Check if it's a template type
    if obj_type in templates:
        return obj_type
        
    raise ValueError(f"Unknown object type: {obj_type}")


def create_core_object(obj_data: Dict[str, Any]) -> BaseKojiObject:
    """
    Create a core koji object from data.
    
    Args:
        obj_data: Object data dictionary
        
    Returns:
        Instantiated core object
        
    Raises:
        ValueError: If object type is not a core model
    """
    
    obj_type = obj_data.get('type')
    if obj_type not in CORE_MODELS:
        raise ValueError(f"'{obj_type}' is not a core model type")
        
    model_class = CORE_MODELS[obj_type]
    return model_class(obj_data)


def expand_template_object(obj_data: Dict[str, Any], templates: Dict[str, Template]) -> List[BaseKojiObject]:
    """
    Expand a template object into core objects.
    
    Args:
        obj_data: Template object data
        templates: Available templates
        
    Returns:
        List of expanded core objects
        
    Raises:
        ValueError: If template type is not found
    """
    
    obj_type = obj_data.get('type')
    if obj_type not in templates:
        raise ValueError(f"Template '{obj_type}' not found")
        
    template = templates[obj_type]
    expanded_data = expand_template(template, obj_data)
    
    # Recursively process expanded objects
    expanded_objects = []
    for expanded_obj_data in expanded_data:
        processed_objects = process_object_data(expanded_obj_data, templates)
        expanded_objects.extend(processed_objects)
        
    return expanded_objects


def process_object_data(obj_data: Dict[str, Any], templates: Dict[str, Template]) -> List[BaseKojiObject]:
    """
    Process object data, handling both core objects and template expansion.
    
    Args:
        obj_data: Object data dictionary
        templates: Available templates
        
    Returns:
        List of processed objects (may be single core object or multiple from template)
    """
    
    if not obj_data.get('name'):
        raise ValueError("Object missing 'name' field")
        
    obj_type = resolve_object_type(obj_data, templates)
    
    if obj_type in CORE_MODELS:
        # Create core object directly
        core_obj = create_core_object(obj_data)
        return [core_obj]
    else:
        # Expand template
        return expand_template_object(obj_data, templates)


def load_object_data(data_dir: str, templates: Dict[str, Template], obj_map: ObjectMap) -> None:
    """
    Load object data from directory and populate object map.
    
    Args:
        data_dir: Path to directory containing data files
        templates: Available templates for expansion
        obj_map: ObjectMap to populate with loaded objects
    """
    
    data_path = Path(data_dir)
    
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
        
    # Process all YAML files in the data directory
    yaml_files = list(data_path.glob("*.yaml")) + list(data_path.glob("*.yml"))
    
    for yaml_file in yaml_files:
        print(f"Loading data from {yaml_file}")
        
        for obj_data in load_yaml_documents(yaml_file):
            try:
                processed_objects = process_object_data(obj_data, templates)
                
                for obj in processed_objects:
                    if obj.key in obj_map:
                        print(f"Warning: Duplicate object {obj.key}, overriding")
                    obj_map.add_object(obj)
                    
            except Exception as e:
                print(f"Error processing object in {yaml_file}: {e}")
                print(f"Object data: {obj_data}")


def validate_object_data(obj_data: Dict[str, Any]) -> bool:
    """
    Validate basic object data structure.
    
    Args:
        obj_data: Object data to validate
        
    Returns:
        True if validation passes
    """
    
    required_fields = ['type', 'name']
    
    for field in required_fields:
        if field not in obj_data:
            print(f"Error: Object missing required field '{field}'")
            return False
            
    return True


def get_object_summary(obj_map: ObjectMap) -> Dict[str, int]:
    """
    Get summary of loaded objects by type.
    
    Args:
        obj_map: ObjectMap to analyze
        
    Returns:
        Dictionary mapping object types to counts
    """
    
    summary = {}
    
    for obj_key, obj in obj_map.items():
        obj_type = obj.type
        if obj_type not in summary:
            summary[obj_type] = 0
        summary[obj_type] += 1
        
    return summary


def print_load_summary(obj_map: ObjectMap) -> None:
    """
    Print a summary of loaded objects.
    
    Args:
        obj_map: ObjectMap to summarize
    """
    
    summary = get_object_summary(obj_map)
    
    print(f"\nLoaded {len(obj_map)} objects:")
    for obj_type, count in sorted(summary.items()):
        print(f"  {obj_type}: {count}")

# The end.
#!/usr/bin/env python3
"""
Generate Sphinx documentation for Pydantic model schemas.

This script creates comprehensive documentation for all core koji object types
by extracting schema information from the Pydantic models.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import koji_habitude
sys.path.insert(0, str(Path(__file__).parent.parent))

from koji_habitude.models import CORE_TYPES


def get_field_type_description(field_info):
    """Get a user-friendly description of a field type."""
    annotation = field_info.annotation

    # Handle generic types
    if hasattr(annotation, '__origin__'):
        origin = annotation.__origin__
        if origin is list:
            args = annotation.__args__
            if args:
                inner_type = args[0].__name__ if hasattr(args[0], '__name__') else str(args[0])
                return f"list of {inner_type}"
            return "list"
        elif origin is dict:
            args = annotation.__args__
            if len(args) >= 2:
                key_type = args[0].__name__ if hasattr(args[0], '__name__') else str(args[0])
                value_type = args[1].__name__ if hasattr(args[1], '__name__') else str(args[1])
                return f"dictionary of {key_type} to {value_type}"
            return "dictionary"
        elif origin is tuple:
            return "tuple"

    # Handle simple types
    if hasattr(annotation, '__name__'):
        type_name = annotation.__name__
        if type_name == 'str':
            return "string"
        elif type_name == 'int':
            return "integer"
        elif type_name == 'bool':
            return "boolean"
        elif type_name == 'float':
            return "number"
        else:
            return type_name

    return str(annotation)


def get_field_default(field_info):
    """Get the default value for a field."""
    if hasattr(field_info, 'default') and field_info.default is not None:
        # Skip PydanticUndefined
        if str(field_info.default) == "PydanticUndefined":
            return None
        if callable(field_info.default):
            if field_info.default.__name__ == 'list':
                return "[]"
            elif field_info.default.__name__ == 'dict':
                return "{}"
            else:
                return f"{field_info.default.__name__}()"
        else:
            return repr(field_info.default)
    return None


def generate_model_doc(model_class, output_dir):
    """Generate Sphinx documentation for a Pydantic model."""

    typename = model_class.typename
    classname = model_class.__name__

    # Create the RST content
    content = f"""{typename.title()} Object Schema
{"=" * (len(typename) + 15)}

The ``{typename}`` type represents a Koji {typename.replace('-', ' ')} object.

Basic Structure
---------------

.. code-block:: yaml

   ---
   type: {typename}
   name: my-{typename.replace('-', '-')}
   # ... {typename}-specific fields

YAML Fields
-----------

"""

    # Add field information from the model
    if hasattr(model_class, 'model_fields'):
        required_fields = []
        optional_fields = []

        for field_name, field_info in model_class.model_fields.items():
            # Skip internal fields and inherited fields
            if field_name in ['name', 'trace', 'yaml_type', 'filename', 'lineno'] or field_name.startswith('__'):
                continue

            # Get the YAML alias (what users actually write)
            yaml_field = field_info.alias or field_name
            field_type_desc = get_field_type_description(field_info)
            default_value = get_field_default(field_info)
            is_required = field_info.is_required()

            # Get field description from docstring or create a reasonable one
            description = field_info.description
            if not description:
                # Create a reasonable description based on field name
                if yaml_field == 'locked':
                    description = "Whether the tag is locked (prevents builds and other modifications)"
                elif yaml_field == 'permission':
                    description = "Permission required to use this tag"
                elif yaml_field == 'arches':
                    description = "List of architectures this tag supports (e.g., ['x86_64', 'aarch64'])"
                elif yaml_field == 'maven-support':
                    description = "Whether Maven support is enabled for this tag"
                elif yaml_field == 'maven-include-all':
                    description = "Whether to include all Maven artifacts in this tag"
                elif yaml_field == 'extras':
                    description = "Additional tag metadata as key-value pairs"
                elif yaml_field == 'groups':
                    description = "Package groups and their package lists"
                elif yaml_field == 'inheritance':
                    description = "List of parent tags with their priorities"
                elif yaml_field == 'external-repos':
                    description = "List of external repositories attached to this tag"
                elif yaml_field == 'capacity':
                    description = "Build capacity for this host"
                elif yaml_field == 'enabled':
                    description = "Whether this host is enabled for builds"
                elif yaml_field == 'comment':
                    description = "Description or comment for this object"
                elif yaml_field == 'usertype':
                    description = "Type of user (0=normal, 1=admin)"
                elif yaml_field == 'status':
                    description = "Status of this object"
                elif yaml_field == 'members':
                    description = "List of members in this group"
                elif yaml_field == 'permissions':
                    description = "List of permissions for this group"
                elif yaml_field == 'channels':
                    description = "List of channels this host is assigned to"
                elif yaml_field == 'hosts':
                    description = "List of hosts assigned to this channel"
                elif yaml_field == 'url':
                    description = "URL for this external repository"
                elif yaml_field == 'build_tag':
                    description = "Build tag for this target"
                elif yaml_field == 'dest_tag':
                    description = "Destination tag for this target"
                else:
                    description = f"Configuration for {yaml_field.replace('-', ' ')}"

            field_info_text = f"``{yaml_field}`` ({field_type_desc})"
            if default_value and default_value != "PydanticUndefined":
                field_info_text += f" - Default: {default_value}"

            if is_required:
                required_fields.append((yaml_field, field_info_text, description))
            else:
                optional_fields.append((yaml_field, field_info_text, description))

        if required_fields:
            content += "Required Fields\n~~~~~~~~~~~~~~~\n\n"
            for yaml_field, field_info_text, description in required_fields:
                content += f"{field_info_text}\n"
                content += f"   {description}\n\n"

        if optional_fields:
            content += "Optional Fields\n~~~~~~~~~~~~~~~\n\n"
            for yaml_field, field_info_text, description in optional_fields:
                content += f"{field_info_text}\n"
                content += f"   {description}\n\n"

    # Add examples section with realistic examples
    content += f"""Examples
--------

Basic {typename.title()}
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   ---
   type: {typename}
   name: my-{typename.replace('-', '-')}
"""

    # Add example fields based on the model
    if hasattr(model_class, 'model_fields'):
        for field_name, field_info in model_class.model_fields.items():
            if field_name == 'name':
                continue
            yaml_field = field_info.alias or field_name
            default_value = get_field_default(field_info)

            if yaml_field == 'locked':
                content += f"   {yaml_field}: false\n"
            elif yaml_field == 'arches':
                content += f"   {yaml_field}:\n"
                content += f"     - x86_64\n"
                content += f"     - aarch64\n"
            elif yaml_field == 'inheritance':
                content += f"   {yaml_field}:\n"
                content += f"     - parent: parent-tag\n"
                content += f"       priority: 10\n"
            elif yaml_field == 'external-repos':
                content += f"   {yaml_field}:\n"
                content += f"     - name: my-repo\n"
                content += f"       priority: 100\n"
            elif yaml_field == 'groups':
                content += f"   {yaml_field}:\n"
                content += f"     my-group:\n"
                content += f"       - package1\n"
                content += f"       - package2\n"
            elif yaml_field == 'extras':
                content += f"   {yaml_field}:\n"
                content += f"     description: \"My {typename} description\"\n"
            elif yaml_field == 'permission':
                content += f"   {yaml_field}: admin\n"
            elif yaml_field == 'maven-support':
                content += f"   {yaml_field}: false\n"
            elif yaml_field == 'maven-include-all':
                content += f"   {yaml_field}: false\n"
            elif yaml_field == 'capacity':
                content += f"   {yaml_field}: 2.0\n"
            elif yaml_field == 'enabled':
                content += f"   {yaml_field}: true\n"
            elif yaml_field == 'comment':
                content += f"   {yaml_field}: \"My {typename} comment\"\n"
            elif yaml_field == 'usertype':
                content += f"   {yaml_field}: 0\n"
            elif yaml_field == 'status':
                content += f"   {yaml_field}: 0\n"
            elif yaml_field == 'members':
                content += f"   {yaml_field}:\n"
                content += f"     - user1\n"
                content += f"     - user2\n"
            elif yaml_field == 'permissions':
                content += f"   {yaml_field}:\n"
                content += f"     - admin\n"
                content += f"     - build\n"
            elif yaml_field == 'channels':
                content += f"   {yaml_field}:\n"
                content += f"     - default\n"
            elif yaml_field == 'hosts':
                content += f"   {yaml_field}:\n"
                content += f"     - buildhost1.example.com\n"
            elif yaml_field == 'url':
                content += f"   {yaml_field}: https://example.com/repo/\n"
            elif yaml_field == 'build_tag':
                content += f"   {yaml_field}: my-build-tag\n"
            elif yaml_field == 'dest_tag':
                content += f"   {yaml_field}: my-dest-tag\n"
            elif yaml_field == 'usertype':
                content += f"   {yaml_field}: 0\n"
            elif yaml_field == 'status':
                content += f"   {yaml_field}: 0\n"

    content += "\n"

    # Add validation rules
    content += """Validation Rules
----------------

- All field types are automatically validated
- Required fields must be present
- Field constraints are enforced (min/max values, string patterns, etc.)
- Duplicate priorities are not allowed in inheritance or external-repos lists

"""

    # Add dependencies section
    if hasattr(model_class, 'dependency_keys'):
        content += """Dependencies
------------

This object type can depend on other objects. Dependencies are automatically
resolved during processing to ensure proper creation order.

"""

    # Add technical reference section
    content += f"""Technical Reference
-------------------

For developers: The ``{typename}`` object is implemented by the
:class:`koji_habitude.models.{typename.replace('-', '_')}.{classname}` class.

"""

    # Write the file
    output_file = output_dir / f"{typename}.rst"
    with open(output_file, 'w') as f:
        f.write(content)

    print(f"Generated documentation for {typename} -> {output_file}")


def main():
    """Generate documentation for all core model types."""

    output_dir = Path(__file__).parent / "yaml_format"
    output_dir.mkdir(exist_ok=True)

    print("Generating Pydantic model documentation...")

    for model_class in CORE_TYPES:
        generate_model_doc(model_class, output_dir)

    print(f"Generated documentation for {len(CORE_TYPES)} model types in {output_dir}")


if __name__ == "__main__":
    main()


# The end.

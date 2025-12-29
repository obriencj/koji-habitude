YAML Format Specification
=========================

koji-habitude uses YAML files to define koji objects and templates. This document
provides a comprehensive reference for the YAML format and schemas for all
supported object types.

File Structure
--------------

YAML files can contain single or multiple documents. Documents are processed
in order, and each document must have a ``type`` field that indicates the
object type.

.. code-block:: yaml

   ---
   type: tag
   name: my-tag
   # ... tag-specific fields

   ---
   type: user
   name: my-user
   # ... user-specific fields

Core Object Types
-----------------

The following core koji object types are supported:

.. toctree::
   :maxdepth: 1

   yaml_format/tag
   yaml_format/target
   yaml_format/user
   yaml_format/group
   yaml_format/host
   yaml_format/channel
   yaml_format/external-repo
   yaml_format/permission
   yaml_format/content-generator
   yaml_format/build-type
   yaml_format/archive-type
   yaml_format/template
   yaml_format/multi

Templates
---------

Templates allow you to define custom object types using Jinja2 templating.
Templates can define data models for validation and type-safe access to template
data. When processing data files, objects with ``type`` matching a template name
trigger template expansion, creating final koji objects through recursive processing.

See :doc:`yaml_format/template` for the full template specification including
model definitions, validation rules, and detailed examples.

Multi Type
----------

The ``multi`` type is a special macro template that expands a single document
containing key-value pairs into multiple YAML documents. This feature exists
primarily to enable the use of YAML anchors across many objects, as YAML
specification does not allow anchors to be shared between separate documents.

See :doc:`yaml_format/multi` for the complete multi type specification including
expansion rules, field descriptions, and detailed examples.

Validation
----------

All objects are validated using Pydantic models with the following features:

- **Type Validation**: Automatic type checking and conversion
- **Field Constraints**: Min/max values, string patterns, list lengths
- **Required Fields**: Automatic validation of required fields
- **Aliases**: Support for field aliases (e.g., ``tag-extras`` vs ``tag_extras``)
- **Custom Validators**: Complex validation logic for koji-specific rules

Error Handling
--------------

When validation fails, koji-habitude provides detailed error messages
including:

- Field names and expected types
- Validation error descriptions
- File and line number information
- Suggested corrections

Example Error Output:

.. code-block:: text

   ValidationError: 1 validation error for Tag
   inheritance.0.priority
     ensure this value is greater than or equal to 0 (type=value_error.number.not_ge; limit_value=0)
     at data/tags.yaml:15:5

Best Practices
--------------

1. **Use Multi-Document Files**: Group related objects in single files
2. **Consistent Naming**: Use consistent naming conventions across objects
3. **Template Organization**: Keep templates in separate files or directories
4. **Validation**: Use schema validation in templates for better error messages
5. **Comments**: Add YAML comments to document complex configurations

.. note::

   All YAML files are processed in dependency order, so you can reference
   objects defined earlier in the same file or in previously processed files.

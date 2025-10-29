template show Command
======================

Show the definition of a single template.

Syntax
------

.. code-block:: bash

   koji-habitude template show [OPTIONS] NAME

Description
-----------

The ``template show`` command displays the definition of a single template,
including its parameters, required fields, optional fields, and other
configuration details. This is useful for understanding what variables a
template expects and how to use it.

The command displays:
- Template name and description
- Required variables (fields that must be provided)
- Optional variables (with default values if any)
- Model information (if the template defines a model)
- Source file location (if ``--full`` is used)

Options
-------

.. option:: NAME

   The name of the template to show. Required.

.. option:: --templates PATH, -t PATH

   Location to find templates. Can be repeated multiple times. If not
   specified, searches the current directory for ``*.yaml`` and ``*.yml``
   files.

.. option:: --recursive, -r

   Search template directories recursively for YAML files.

.. option:: --yaml

   Show the template definition as YAML instead of formatted text output.

.. option:: --full

   Show full template details including:
   - Source file location and line number
   - Expansion trace (if template was expanded from another template)
   - Template content (for inline templates)

Examples
--------

Show a template from current directory:

.. code-block:: bash

   koji-habitude template show fedora-build

Show template from specific directory:

.. code-block:: bash

   koji-habitude template show --templates templates/ fedora-build

Show template as YAML:

.. code-block:: bash

   koji-habitude template show --yaml fedora-build

Show full details including source file:

.. code-block:: bash

   koji-habitude template show --full fedora-build

Show template with recursive search:

.. code-block:: bash

   koji-habitude template show --recursive --templates templates/ rhel-build

Use Cases
---------

- **Quick Reference**: Quickly check what parameters a template needs
- **Documentation**: Generate template reference documentation
- **Debugging**: Verify template definition is correct
- **Learning**: Understand how templates are structured

Related Commands
----------------

- :doc:`../list-templates` - List all available templates
- :doc:`expand` - Expand the template with variables

Exit Codes
----------

- ``0`` - Success
- ``1`` - Template not found

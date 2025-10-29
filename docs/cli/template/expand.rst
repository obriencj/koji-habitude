template expand Command
========================

Expand a single template and show the result.

Syntax
------

.. code-block:: bash

   koji-habitude template expand [OPTIONS] NAME [KEY=VALUE...]

Description
-----------

The ``template expand`` command expands a single template with the given
variable assignments and outputs the resulting YAML. This allows you to
test template expansion without creating data files or connecting to Koji.

The command:
1. Loads the specified template
2. Applies variable assignments from ``KEY=VALUE`` arguments
3. Expands the template using Jinja2
4. Outputs the resulting YAML objects

This is useful for:
- Testing template logic
- Previewing template expansion
- Debugging template issues
- Understanding what a template produces

Options
-------

.. option:: NAME

   The name of the template to expand. Required.

.. option:: KEY=VALUE

   Variable assignments for template expansion. Can be repeated multiple times.
   If a variable is specified without ``=``, it is treated as ``KEY=`` (empty value).

.. option:: --templates PATH, -t PATH

   Location to find templates. Can be repeated multiple times. If not
   specified, searches the current directory for ``*.yaml`` and ``*.yml`` files.

.. option:: --recursive, -r

   Search template directories recursively for YAML files.

.. option:: --validate

   Validate the expanded template using Pydantic models. When enabled, outputs
   fully validated objects. When disabled (default), outputs raw expanded data.

Examples
--------

Expand a simple template:

.. code-block:: bash

   koji-habitude template expand fedora-build name=fedora-42-build

Expand with multiple variables:

.. code-block:: bash

   koji-habitude template expand fedora-build name=fedora-42-build version=42 release=1

Expand with validation:

.. code-block:: bash

   koji-habitude template expand --validate fedora-build name=fedora-42-build

Expand template from specific directory:

.. code-block:: bash

   koji-habitude template expand --templates templates/ my-template name=test

Expand with empty value:

.. code-block:: bash

   koji-habitude template expand my-template optional_field= required_field=value

Expand and save to file:

.. code-block:: bash

   koji-habitude template expand fedora-build name=test > output.yaml

Use Cases
---------

- **Testing**: Test template expansion logic quickly
- **Debugging**: Debug template issues without full workflow
- **Preview**: See what a template produces before using it in data files
- **Documentation**: Generate examples of template usage

Related Commands
----------------

- :doc:`../expand` - Expand multiple templates from data files
- :doc:`show` - Show template definition
- :doc:`compare` - Expand and compare with Koji state

Exit Codes
----------

- ``0`` - Success
- ``1`` - Error (e.g., template not found, validation failure)

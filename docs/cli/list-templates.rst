list-templates Command
======================

List available templates with their configuration details.

Syntax
------

.. code-block:: bash

   koji-habitude list-templates [OPTIONS] [PATH...]

Description
-----------

The ``list-templates`` command shows all templates found in the given
locations with their configuration details. This is useful for:

- Discovering available templates
- Understanding template parameters and requirements
- Verifying template definitions are loaded correctly
- Getting template information for documentation

The command accepts both ``--templates`` options and positional PATH
arguments to accommodate different invocation patterns. Positional paths
are treated the same as ``--templates`` options.

Options
-------

.. option:: PATH

   Optional. Directories containing template files. Treated the same as
   ``--templates`` options. Can be repeated multiple times.

.. option:: --templates PATH, -t PATH

   Load only templates from the given paths. Can be repeated multiple times.

.. option:: --recursive, -r

   Search template directories recursively for YAML files.

.. option:: --yaml

   Show expanded templates as YAML instead of formatted text output.

.. option:: --full

   Show full template details including source file locations and expansion
   trace information.

.. option:: --select NAME, -S NAME

   Select templates by name. Can be repeated multiple times. Only selected
   templates will be shown.

Examples
--------

List templates in current directory:

.. code-block:: bash

   koji-habitude list-templates

List templates from specific directories:

.. code-block:: bash

   koji-habitude list-templates templates/ shared-templates/

List templates using --templates option:

.. code-block:: bash

   koji-habitude list-templates --templates templates/ --templates shared/

List with recursive search:

.. code-block:: bash

   koji-habitude list-templates --recursive templates/

List with full details:

.. code-block:: bash

   koji-habitude list-templates --full templates/

List specific templates by name:

.. code-block:: bash

   koji-habitude list-templates --select fedora-build --select rhel-build

Show templates as YAML:

.. code-block:: bash

   koji-habitude list-templates --yaml templates/

Use Cases
---------

- **Discovery**: Find out what templates are available
- **Documentation**: Generate template reference documentation
- **Debugging**: Verify templates are loaded correctly
- **Inspecting**: Understand template parameters and requirements

Related Commands
----------------

- :doc:`template/show` - Show detailed information about a single template
- :doc:`template/expand` - Expand a template with variables

Exit Codes
----------

- ``0`` - Success
- ``1`` - Error (e.g., template files not found)

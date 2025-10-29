template compare Command
==========================

Expand a single template and compare the result with Koji (dry-run).

Syntax
------

.. code-block:: bash

   koji-habitude template compare [OPTIONS] NAME [KEY=VALUE...]

Description
-----------

The ``template compare`` command expands a single template with given
variables and compares the expanded objects with the objects on the Koji
instance. This is a dry-run operation that never modifies Koji - it only
shows what differences would exist.

The command:
1. Loads and expands the template with provided variables
2. Connects to the Koji hub instance
3. Compares expanded objects against remote state
4. Displays a summary of differences

This is useful for:
- Previewing changes before applying a template
- Validating template expansion produces correct objects
- Understanding what would change in Koji
- Testing template variables

Options
-------

.. option:: NAME

   The name of the template to expand and compare. Required.

.. option:: KEY=VALUE

   Variable assignments for template expansion. Can be repeated multiple times.
   If a variable is specified without ``=``, it is treated as ``KEY=`` (empty value).

.. option:: --templates PATH, -t PATH

   Location to find templates. Can be repeated multiple times. If not
   specified, searches the current directory for ``*.yaml`` and ``*.yml`` files.

.. option:: --recursive, -r

   Search template directories recursively for YAML files.

.. option:: --profile PROFILE, -p PROFILE

   Koji profile to use for connection. Default: ``koji``.

.. option:: --show-unchanged

   Show objects that don't need any changes in the summary output.
   By default, only objects with differences are shown.

Examples
--------

Compare a template expansion with Koji:

.. code-block:: bash

   koji-habitude template compare fedora-build name=fedora-42-build

Compare with multiple variables:

.. code-block:: bash

   koji-habitude template compare fedora-build name=fedora-42-build version=42 release=1

Compare showing unchanged objects:

.. code-block:: bash

   koji-habitude template compare --show-unchanged fedora-build name=fedora-42-build

Compare against specific profile:

.. code-block:: bash

   koji-habitude template compare --profile staging fedora-build name=test

Compare template from specific directory:

.. code-block:: bash

   koji-habitude template compare --templates templates/ my-template name=test

Use Cases
---------

- **Pre-Flight Check**: Preview what would change before applying
- **Template Testing**: Test template variables against real Koji state
- **Validation**: Verify template expansion produces expected objects
- **Change Review**: Review proposed template usage before applying

Related Commands
----------------

- :doc:`apply` - Apply the template after comparing
- :doc:`diff` - Show unified diff format of differences
- :doc:`expand` - Expand template without comparing

Exit Codes
----------

- ``0`` - No phantom dependencies detected
- ``1`` - Phantom dependencies found (objects referenced but not defined)

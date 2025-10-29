template apply Command
========================

Apply a single template expansion to Koji.

Syntax
------

.. code-block:: bash

   koji-habitude template apply [OPTIONS] NAME [KEY=VALUE...]

Description
-----------

The ``template apply`` command expands a single template with given variables
and applies the expanded objects to the Koji instance. This allows you to
apply template-based changes without creating full data files.

The command:
1. Loads and expands the template with provided variables
2. Resolves dependencies between objects
3. Connects to the Koji hub instance
4. Compares expanded objects against remote state
5. Applies changes in dependency-resolved order
6. Displays a summary of changes made

This is useful for:
- Quick template-based updates
- Testing template application
- One-off template deployments
- Scripting template-based changes

.. warning::

   This command **will modify** your Koji instance. Always use
   ``template compare`` or ``template diff`` first to preview changes.

Options
-------

.. option:: NAME

   The name of the template to expand and apply. Required.

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
   Useful for auditing the full state of objects.

Examples
--------

Apply a template expansion:

.. code-block:: bash

   koji-habitude template apply fedora-build name=fedora-42-build

Apply with multiple variables:

.. code-block:: bash

   koji-habitude template apply fedora-build name=fedora-42-build version=42 release=1

Apply template from specific directory:

.. code-block:: bash

   koji-habitude template apply --templates templates/ my-template name=test

Apply to specific profile:

.. code-block:: bash

   koji-habitude template apply --profile staging fedora-build name=test

Apply showing unchanged objects:

.. code-block:: bash

   koji-habitude template apply --show-unchanged fedora-build name=fedora-42-build

Safe Workflow Example:

.. code-block:: bash

   # First, preview changes
   koji-habitude template compare fedora-build name=fedora-42-build

   # Review the diff
   koji-habitude template diff fedora-build name=fedora-42-build

   # Apply if everything looks good
   koji-habitude template apply fedora-build name=fedora-42-build

Use Cases
---------

- **Quick Updates**: Apply template-based changes quickly
- **Scripting**: Automate template-based deployments
- **Testing**: Test template application workflow
- **One-offs**: Apply templates without creating data files

Related Commands
----------------

- :doc:`compare` - Preview changes before applying (dry-run)
- :doc:`diff` - Show unified diff of changes
- :doc:`expand` - Expand template without applying

Exit Codes
----------

- ``0`` - Success, all changes applied
- ``1`` - Error encountered (e.g., phantom dependencies, validation failures)

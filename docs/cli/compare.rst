compare Command
===============

Show what changes would be made without applying them (dry-run).

Syntax
------

.. code-block:: bash

   koji-habitude compare [OPTIONS] DATA [DATA...]

Description
-----------

The ``compare`` command performs the same processing as ``apply`` but without
making any changes to the Koji hub. It provides detailed change analysis and
dependency reporting, making it ideal for:

- Previewing changes before applying them
- Validating your YAML definitions
- Understanding what would change in your Koji instance
- Checking for phantom dependencies

The command will:

1. Load all templates and data files
2. Resolve dependencies between objects
3. Connect to the Koji hub instance
4. Compare local definitions with remote state
5. Display a summary of differences
6. Show resolver report (including any phantom dependencies)

This is a safe, read-only operation that never modifies the Koji instance.

Options
-------

.. option:: DATA

   One or more directories or files containing YAML object definitions.
   Required. Can be repeated multiple times.

.. option:: --templates PATH, -t PATH

   Location to find templates that are not available in DATA directories.
   Can be repeated multiple times.

.. option:: --recursive, -r

   Search template and data directories recursively for YAML files.

.. option:: --profile PROFILE, -p PROFILE

   Koji profile to use for connection. Default: ``koji``.

.. option:: --show-unchanged

   Show objects that don't need any changes in the summary output.
   By default, only objects with differences are shown.

Examples
--------

Compare a data directory against Koji:

.. code-block:: bash

   koji-habitude compare data/

Preview changes with templates from multiple locations:

.. code-block:: bash

   koji-habitude compare --templates templates/ --templates shared/ data/

Compare with recursive search:

.. code-block:: bash

   koji-habitude compare --recursive data/ tags/ targets/

Show all objects including unchanged ones:

.. code-block:: bash

   koji-habitude compare --show-unchanged data/

Compare against a specific Koji profile:

.. code-block:: bash

   koji-habitude compare --profile staging data/

Use Cases
---------

- **Pre-Flight Check**: Always run ``compare`` before ``apply`` to review changes
- **Validation**: Verify your YAML definitions are correct before deployment
- **Change Review**: Review proposed changes as part of a code review process
- **Dependency Analysis**: Identify missing dependencies (phantoms) before applying

Related Commands
----------------

- :doc:`apply` - Apply the changes (after reviewing with compare)
- :doc:`diff` - Show unified diff format of differences
- :doc:`fetch` - Fetch remote state for offline comparison

Exit Codes
----------

- ``0`` - No phantom dependencies detected
- ``1`` - Phantom dependencies found (objects referenced but not defined)

apply Command
==============

Apply local koji data expectations onto the hub instance.

Syntax
------

.. code-block:: bash

   koji-habitude apply [OPTIONS] DATA [DATA...]

Description
-----------

The ``apply`` command loads templates and data files, resolves dependencies,
and applies changes to the koji hub in the correct order. This is the primary
command for synchronizing your local YAML definitions with a Koji instance.

The command will:

1. Load all templates from specified locations
2. Load and expand all data files
3. Resolve dependencies between objects (e.g., tag inheritance)
4. Connect to the Koji hub instance
5. Compare local definitions with remote state
6. Apply changes in dependency-resolved order
7. Display a summary of changes made

If phantom dependencies are detected (objects referenced but not defined),
the command will exit with an error code and display the resolver report.

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
   Useful for auditing the full state of objects.

.. option:: --skip-phantoms

   Skip objects that have phantom dependencies instead of exiting with an
   error. Use with caution, as this may lead to incomplete synchronization.

Examples
--------

Apply all objects from a data directory:

.. code-block:: bash

   koji-habitude apply data/

Apply with additional template locations:

.. code-block:: bash

   koji-habitude apply --templates templates/ --templates shared-templates/ data/

Apply with recursive search and show unchanged objects:

.. code-block:: bash

   koji-habitude apply --recursive --show-unchanged data/ tags/

Apply using a specific Koji profile:

.. code-block:: bash

   koji-habitude apply --profile production data/prod/

Skip phantom dependencies (use with caution):

.. code-block:: bash

   koji-habitude apply --skip-phantoms data/

Use Cases
---------

- **Initial Setup**: Apply a full set of koji objects to a new or empty instance
- **Continuous Sync**: Regularly synchronize local changes with the hub
- **Selective Updates**: Apply changes from specific directories or files
- **Audit Trail**: Use ``--show-unchanged`` to see all objects and their status

Related Commands
----------------

- :doc:`compare` - Preview changes without applying them (dry-run)
- :doc:`fetch` - Fetch remote state as YAML for comparison
- :doc:`diff` - Show unified diff of changes

Exit Codes
----------

- ``0`` - Success, all changes applied
- ``1`` - Error encountered (e.g., phantom dependencies, validation failures)

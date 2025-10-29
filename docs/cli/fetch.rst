fetch Command
==============

Fetch remote data from Koji instance and output as YAML.

Syntax
------

.. code-block:: bash

   koji-habitude fetch [OPTIONS] DATA [DATA...]

Description
-----------

The ``fetch`` command produces YAML that reflects the remote state of locally
defined objects. By default, only objects that differ from local definitions are
shown, but ``--show-unchanged`` can be used to fetch all objects.

The semantics of this command are complementary to ``compare``, but rather than
comparing local vs remote state, it focuses on producing that remote state in a
YAML format.

This command is useful for:

- Exporting or backing up current Koji state
- Bootstrapping local definitions from existing instances
- Comparing local vs remote state
- Auditing Koji configuration

The command will:

1. Load templates and data files from local paths
2. Resolve dependencies and identify objects
3. Connect to the Koji hub instance
4. Fetch remote state for all identified objects
5. Output YAML representing remote state
6. Filter to only differing objects (unless ``--show-unchanged`` is used)

Options
-------

.. option:: DATA

   One or more directories or files containing YAML object definitions.
   Required. Can be repeated multiple times. These define which objects
   to fetch from Koji.

.. option:: --templates PATH, -t PATH

   Location to find templates that are not available in DATA directories.
   Can be repeated multiple times.

.. option:: --recursive, -r

   Search template and data directories recursively for YAML files.

.. option:: --profile PROFILE, -p PROFILE

   Koji profile to use for connection. Default: ``koji``.

.. option:: --output PATH, -o PATH

   Path to output YAML file. Default: stdout.

.. option:: --include-defaults, -d

   Include default values in the output. By default, default values are
   excluded.

.. option:: --show-unchanged, -u

   Show all objects from the data series, regardless of whether they differ
   from local definitions. By default, only objects that differ are shown.

Examples
--------

Fetch remote state of objects defined in data directory:

.. code-block:: bash

   koji-habitude fetch data/

Fetch the remote state for all objects declared in the data directory and output
their yaml, including content that would not be overwritten by values in the
local definitions:

.. code-block:: bash

   koji-habitude fetch --show-unchanged data/


Use Cases
---------

- **Backup**: Create YAML backups of your Koji configuration
- **Audit**: See what actually exists in Koji vs. what you've defined locally
- **Migration**: Export state from one Koji instance for import to another
- **Comparison**: Fetch remote state for offline comparison with local definitions
- **Bootstrap**: Use as starting point for creating local YAML definitions

Related Commands
----------------

- :doc:`dump` - Bootstrap local definitions using pattern matching (no local files needed)
- :doc:`compare` - Compare local vs remote state with detailed analysis
- :doc:`apply` - Apply local changes to Koji

Exit Codes
----------

- ``0`` - Success

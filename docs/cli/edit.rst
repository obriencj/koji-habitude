edit Command
============

Edit remote koji objects interactively using an editor.

Syntax
------

.. code-block:: bash

   koji-habitude edit [OPTIONS] NAMES [NAMES...]

Description
-----------

The ``edit`` command loads remote objects from a Koji instance, opens them in
your system editor for interactive editing, validates the changes, shows a
delta comparison, and optionally applies them. This is ideal for making quick
changes to existing koji objects without needing to maintain local YAML files.

The command will:

1. Connect to the Koji hub instance (read-only, no authentication required)
2. Load the specified remote objects
3. Convert them to YAML format
4. Open them in your system editor (via ``$EDITOR`` environment variable)
5. Validate the edited YAML after each save
6. Show a comparison of changes (delta) against the remote state
7. Prompt for action: [A]pply / [E]dit / [Q]uit

The interactive workflow allows you to:

- Edit objects multiple times until satisfied
- Review changes before applying
- Cancel at any time without making changes
- See validation errors and retry editing

If validation errors occur (YAML parsing or object validation), you can choose
to edit again or quit. The editor will be re-opened with the last edited content
so you can fix the issues.

Options
-------

.. option:: NAMES

   One or more object names to edit. Required. Can be specified in two formats:

   - ``TYPE:NAME`` - Explicitly specify the object type and name
     (e.g., ``tag:foo``, ``user:bob``, ``target:build-target``)

   - ``NAME`` - Use the default type (specified with ``--type``, defaults to
     ``tag``) for untyped names (e.g., ``foo`` becomes ``tag:foo``)

   Can be repeated multiple times to edit multiple objects at once.

.. option:: --templates PATH, -t PATH

   Location to find templates that are not available in DATA directories.
   Can be repeated multiple times.

.. option:: --profile PROFILE, -p PROFILE

   Koji profile to use for connection. Default: ``koji``.

.. option:: --include-defaults, -d

   Include default values in the YAML output. By default, fields with default
   values are omitted to keep the YAML concise. Use this flag to see all fields,
   including those with default values.

.. option:: --type TYPE

   Default type to use for untyped names (names without ``TYPE:`` prefix).
   Default: ``tag``. Must be one of the core koji object types.

.. option:: --show-unchanged

   Show objects that don't need any changes in the comparison output.
   By default, only objects with differences are shown.

.. option:: --skip-phantoms

   Skip objects that have phantom dependencies instead of exiting with an
   error. Use with caution, as this may lead to incomplete synchronization.

Examples
--------

Edit a single tag:

.. code-block:: bash

   koji-habitude edit tag:foo

Edit multiple objects of different types:

.. code-block:: bash

   koji-habitude edit tag:foo user:bob target:build-target

Edit objects using default type (tag):

.. code-block:: bash

   koji-habitude edit foo bar

Edit targets using default type:

.. code-block:: bash

   koji-habitude edit build-target dest-target --type=target

Edit with all default values included:

.. code-block:: bash

   koji-habitude edit tag:foo --include-defaults

Edit using a specific Koji profile:

.. code-block:: bash

   koji-habitude edit --profile production tag:prod-tag

Show all objects including unchanged ones:

.. code-block:: bash

   koji-habitude edit tag:foo --show-unchanged

Use Cases
---------

- **Quick Edits**: Make small changes to existing koji objects without
  maintaining local YAML files
- **Interactive Exploration**: Load remote objects to see their current state
  and structure
- **One-Off Changes**: Modify objects that don't warrant creating or updating
  data files
- **Learning Tool**: Examine how koji objects are represented in YAML format
- **Emergency Fixes**: Quickly fix misconfigured objects directly from the
  command line

Related Commands
---------------

- :doc:`apply` - Apply changes from local YAML files
- :doc:`compare` - Preview changes without applying (dry-run)
- :doc:`fetch` - Fetch remote state as YAML files for offline editing

Exit Codes
----------

- ``0`` - Success (changes applied) or edit cancelled by user
- ``1`` - Error encountered (e.g., invalid object type, no objects found,
  validation failures)

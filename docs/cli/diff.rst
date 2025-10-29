diff Command
=============

Show unified diff between local and remote YAML objects.

Syntax
------

.. code-block:: bash

   koji-habitude diff [OPTIONS] DATA [DATA...]

Description
-----------

The ``diff`` command compares local definitions against remote koji state and
displays a unified diff for objects that differ. This provides a familiar
diff-style output that is easy to read and review, similar to ``git diff``.

It's important to note that this command is only comparing the state in a direct
mannar. Features like the ``exact_packages`` setting on a Tag -- which would
allow a remote tag to have packages that are not declared in the local
definitions -- are not considered by this command. The unified diff would still
represent those packages as a potential removal, despite the fact that the
``apply`` command would not remove them.

The command will:

1. Load all templates and data files
2. Resolve dependencies between objects
3. Connect to the Koji hub instance
4. Compare local definitions with remote state
5. Display unified diff format showing differences

Useful for:
- Quick visual inspection of differences
- Integration with diff-based tools and workflows
- Code review processes that expect diff output
- Scripting and automation that parse diff output

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

.. option:: --include-defaults, -d

   Include default values in the diff output. By default, default values
   are excluded to focus on meaningful differences.

.. option:: --context N, -c N

   Number of context lines around each change. Default: ``3``. Increase
   for more context, decrease for more compact output.

Examples
--------

Show diff for a data directory:

.. code-block:: bash

   koji-habitude diff data/

Show diff with more context lines:

.. code-block:: bash

   koji-habitude diff --context 5 data/

Include default values in the diff:

.. code-block:: bash

   koji-habitude diff --include-defaults data/

Diff with recursive search and templates:

.. code-block:: bash

   koji-habitude diff --recursive --templates templates/ data/

Show diff against a specific profile:

.. code-block:: bash

   koji-habitude diff --profile staging data/

Use Cases
---------

- **Change Review**: Get a quick diff-style view of what would change
- **Code Review**: Include diff output in pull requests for review
- **CI/CD Integration**: Parse diff output in automated workflows
- **Audit Logs**: Generate diff-based reports of configuration changes

Related Commands
----------------

- :doc:`compare` - Detailed change analysis without diff format
- :doc:`apply` - Apply the changes shown in the diff

Exit Codes
----------

- ``0`` - No differences found (or diffcount is zero)
- ``1`` - Differences found

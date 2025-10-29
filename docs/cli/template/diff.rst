template diff Command
======================

Expand a single template and show unified diff with Koji state.

Syntax
------

.. code-block:: bash

   koji-habitude template diff [OPTIONS] NAME [KEY=VALUE...]

Description
-----------

The ``template diff`` command expands a single template with given variables
and displays a unified diff between the expanded and validated template and
the koji state of the expanded objects. This provides a familiar diff-style
output that is easy to read and review.

The command:
1. Loads and expands the template with provided variables
2. Connects to the Koji hub instance
3. Compares expanded objects against remote state
4. Displays unified diff format showing differences

This is useful for:
- Quick visual inspection of differences
- Integration with diff-based tools and workflows
- Code review processes
- Scripting and automation

Options
-------

.. option:: NAME

   The name of the template to expand and diff. Required.

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

.. option:: --include-defaults, -d

   Include default values in the diff output. By default, default values
   are excluded to focus on meaningful differences.

.. option:: --context N, -c N

   Number of context lines around each change. Default: ``3``. Increase
   for more context, decrease for more compact output.

Examples
--------

Show diff for a template expansion:

.. code-block:: bash

   koji-habitude template diff fedora-build name=fedora-42-build

Show diff with more context:

.. code-block:: bash

   koji-habitude template diff --context 5 fedora-build name=fedora-42-build

Show diff including defaults:

.. code-block:: bash

   koji-habitude template diff --include-defaults fedora-build name=fedora-42-build

Show diff against specific profile:

.. code-block:: bash

   koji-habitude template diff --profile staging fedora-build name=test

Show diff with multiple variables:

.. code-block:: bash

   koji-habitude template diff my-template name=test version=1 release=2

Use Cases
---------

- **Change Review**: Get a quick diff-style view of what would change
- **Code Review**: Include diff output in pull requests
- **CI/CD Integration**: Parse diff output in automated workflows
- **Audit Logs**: Generate diff-based reports

Related Commands
----------------

- :doc:`compare` - Detailed change analysis without diff format
- :doc:`apply` - Apply the template after reviewing the diff

Exit Codes
----------

- ``0`` - No differences found (or diffcount is zero)
- ``1`` - Differences found

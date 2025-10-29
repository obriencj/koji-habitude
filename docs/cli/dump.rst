dump Command
=============

Bootstrap local definitions from remote Koji state using pattern matching.

Syntax
------

.. code-block:: bash

   koji-habitude dump [OPTIONS] PATTERNS...

Description
-----------

The ``dump`` command searches Koji for objects matching given patterns and
outputs their remote state as YAML. Unlike ``fetch``, which requires local
YAML definitions, ``dump`` operates entirely on remote data using pattern
matching.

This command is particularly useful for:

- Bootstrapping local YAML definitions from an existing Koji instance
- Discovering objects by name patterns
- Exporting specific objects or sets of objects
- Creating local definitions without having existing YAML

The command supports:

- **Typed patterns**: ``tag:foo``, ``user:*bob*``, ``target:*-build``
- **Untyped patterns**: ``*-build`` (applied to default types)
- **Glob patterns**: Wildcards (``*``, ``?``, character classes ``[]``)
- **Exact matches**: Direct object names
- **Dependency resolution**: Optionally include related objects

Options
-------

.. option:: PATTERNS

   One or more search patterns. Required. Patterns can be:

   - Typed: ``type:pattern`` (e.g., ``tag:foo``, ``user:*bob*``)
   - Untyped: ``pattern`` (applied to default types)

   Can be repeated multiple times for multiple patterns.

.. option:: --profile PROFILE, -p PROFILE

   Koji profile to use for connection. Default: ``koji``.

.. option:: --output PATH, -o PATH

   Path to output YAML file. Default: stdout.

.. option:: --include-defaults, -d

   Include default values in output. By default, default values are excluded.

.. option:: --with-deps

   Include dependencies of matched objects. For example, if dumping a tag,
   also include its parent tags and external repositories.

.. option:: --with-dep-type TYPE

   Limit dependencies to specific types. Can be repeated for multiple types.
   If specified, ``--with-deps`` is automatically enabled.

   Valid types: ``tag``, ``target``, ``user``, ``host``

.. option:: --max-depth N

   Maximum dependency depth when using ``--with-deps``. Default: unlimited.
   Limits how many levels of dependencies to follow.

.. option:: --tags

   Search tags by default for untyped patterns.

.. option:: --targets

   Search targets by default for untyped patterns.

.. option:: --users

   Search users by default for untyped patterns.

.. option:: --hosts

   Search hosts by default for untyped patterns.

Pattern Examples
----------------

Typed patterns:
   ``tag:fedora-42-build``
      Exact match for tag named "fedora-42-build"

   ``user:*bob*``
      All users with "bob" in their name (wildcard pattern)

   ``target:*-build``
      All targets ending in "-build"

Untyped patterns (use default types):
   ``*-build``
      Matches tags and targets (default) ending in "-build"

   ``f40-*``
      Matches default types starting with "f40-"

Mixed patterns:
   ``tag:foo target:bar *-build user:*admin*``
      Combination of typed and untyped patterns

Examples
--------

Search tags and targets for patterns (default behavior):

.. code-block:: bash

   koji-habitude dump *-build

Search specific types only:

.. code-block:: bash

   koji-habitude dump --tags --users *bob*

Exact tag match with dependencies:

.. code-block:: bash

   koji-habitude dump tag:f40-build --with-deps

Dependencies with depth limit:

.. code-block:: bash

   koji-habitude dump tag:f40-build --with-deps --max-depth 2

Dependencies only for specific types:

.. code-block:: bash

   koji-habitude dump tag:f40-build --with-deps --with-dep-type tag --with-dep-type external-repo

Mixed patterns:

.. code-block:: bash

   koji-habitude dump tag:foo target:bar *-build user:*admin*

Save output to file:

.. code-block:: bash

   koji-habitude dump --output my-tags.yaml *-build

Include default values:

.. code-block:: bash

   koji-habitude dump --include-defaults tag:foo

Use Cases
---------

- **Bootstrap**: Create initial YAML definitions from existing Koji instance
- **Migration**: Export objects from one instance for import to another
- **Audit**: Discover and document what exists in Koji
- **Backup**: Create YAML backups of specific object sets
- **Pattern Discovery**: Find objects by name patterns

Related Commands
----------------

- :doc:`fetch` - Fetch remote state for objects defined in local YAML files
- :doc:`apply` - Apply YAML definitions to Koji

Exit Codes
----------

- ``0`` - Success
- ``1`` - Error (e.g., invalid pattern, invalid type)

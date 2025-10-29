expand Command
==============

Expand templates and data files into YAML output.

Syntax
------

.. code-block:: bash

   koji-habitude expand [OPTIONS] DATA [DATA...]

Description
-----------

The ``expand`` command loads templates from specified locations, processes
data files through template expansion, and outputs the final YAML content
to stdout. This is useful for:

- Previewing template expansion without connecting to Koji
- Generating intermediate YAML for debugging
- Validating template expansion logic
- Creating static YAML from dynamic templates
- Integration with other tools that consume YAML

The command performs:

1. Load templates from ``--templates`` locations
2. Load and process data files
3. Expand templates using Jinja2
4. Validate expanded objects (if ``--validate`` is used)
5. Output final YAML to stdout

Note: This command does **not** connect to Koji and does not modify any
remote state. It's a purely local operation.

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

.. option:: --validate

   Validate the expanded templates and data files using Pydantic models.
   When enabled, outputs fully validated objects. When disabled (default),
   outputs raw expanded data.

.. option:: --include-defaults, -d

   Include default values in output. By default, default values are excluded.
   Only applies when ``--validate`` is used.

.. option:: --no-comments

   Do not include comments in the YAML output. Comments are included by default.

.. option:: --select TYPE, -S TYPE

   Filter results to only include objects of the specified type(s).
   Can be repeated multiple times to select multiple types.

Examples
--------

Expand templates and data files:

.. code-block:: bash

   koji-habitude expand data/

Expand with validation enabled:

.. code-block:: bash

   koji-habitude expand --validate data/

Expand and save to a file:

.. code-block:: bash

   koji-habitude expand data/ > expanded.yaml

Expand only specific object types:

.. code-block:: bash

   koji-habitude expand --select tag --select target data/

Expand with templates from multiple locations:

.. code-block:: bash

   koji-habitude expand --templates templates/ --templates shared/ data/

Expand without comments:

.. code-block:: bash

   koji-habitude expand --no-comments data/ | some-tool

Expand with recursive search:

.. code-block:: bash

   koji-habitude expand --recursive data/ tags/

Use Cases
---------

- **Template Debugging**: See exactly what templates expand to
- **Pre-Processing**: Generate static YAML from dynamic templates
- **Validation**: Use ``--validate`` to check template expansion correctness
- **Type Filtering**: Extract specific object types using ``--select``
- **Integration**: Pipe output to other tools that consume YAML

Related Commands
----------------

- :doc:`apply` - Apply expanded objects to Koji
- :doc:`compare` - Compare expanded objects against Koji state
- :doc:`template/expand` - Expand a single template with variables

Exit Codes
----------

- ``0`` - Success
- ``1`` - Error (e.g., validation failure, missing templates)

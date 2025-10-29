Template Subcommands
=====================

The ``template`` command group provides operations for working with individual
templates by name. These commands allow you to inspect, expand, compare, and
apply single templates without working with full data file collections.

Unlike the primary commands that operate on collections of objects, template
subcommands work with a specific template and allow you to provide variables
directly on the command line using ``KEY=VALUE`` syntax.

Overview
--------

Template subcommands follow this pattern:

.. code-block:: bash

   koji-habitude template COMMAND [OPTIONS] NAME [KEY=VALUE...]

Where:
- ``COMMAND`` is one of: ``show``, ``expand``, ``compare``, ``diff``, ``apply``
- ``NAME`` is the name of the template to work with
- ``KEY=VALUE`` pairs provide variables for template expansion

Common Options
--------------

All template subcommands share these options:

``--templates PATH``, ``-t PATH``
   Location to find templates. Can be repeated multiple times. If not specified,
   the command searches the current directory for ``*.yaml`` and ``*.yml`` files.

``--recursive``, ``-r``
   Search template directories recursively for YAML files.

``--profile PROFILE``, ``-p PROFILE``
   Koji profile to use for connection. Default: ``koji``. Applies to commands
   that connect to Koji (``compare``, ``diff``, ``apply``).

Commands
--------

.. toctree::
   :maxdepth: 1

   show
   expand
   compare
   diff
   apply

Related Documentation
---------------------

- :doc:`../../yaml_format/template` - Template YAML format specification
- :doc:`../list-templates` - List all available templates

Command-Line Interface
======================

koji-habitude provides a comprehensive command-line interface for managing
Koji objects through YAML templates and data files. All commands are built
using `Click <https://click.palletsprojects.com/>`__.

Overview
--------

The CLI is organized into primary commands for working with collections of
objects, and a ``template`` subcommand group for working with individual
templates by name.

Primary Commands
----------------

The main commands operate on collections of YAML files:

.. toctree::
   :maxdepth: 1

   apply
   compare
   diff
   expand
   fetch
   dump
   list-templates

Template Commands
-----------------

Work with individual templates by name:

.. toctree::
   :maxdepth: 1

   template/index

Common Options
--------------

Many commands share common options:

``--templates PATH``, ``-t PATH``
   Location to find templates that are not available in the DATA directories.
   This option can be repeated multiple times to specify multiple template
   locations. The template paths use the same format as the DATA paths, the
   difference being that all non-template objects defined in the template path
   are ignored.

``--recursive``, ``-r``
   Search template and data directories recursively for YAML files.

``--profile PROFILE``, ``-p PROFILE``
   Koji profile to use for connection. Defaults to ``koji`` if not specified.

``--show-unchanged``
   Include objects in output that don't need any changes. Useful for
   auditing and understanding the full state of objects.

Argument Conventions
--------------------

``DATA``
   One or more directories or files containing YAML object definitions.
   Directories are searched for ``*.yaml`` and ``*.yml`` files. Any YAML files
   found can contribute both objects and templates.

``NAME``
   The name of a template when working with template subcommands.


Related Documentation
----------------------

- :doc:`../yaml_format` - YAML format specification
- :doc:`../overview` - Project overview and architecture

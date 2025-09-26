koji-habitude
=============

   **⚠️ Work In Progress**: This project is currently under development.
   Core architecture is largely complete including CLI framework, data
   models, and dependency resolution, but synchronization with Koji hubs
   is not yet implemented.

Current Status
--------------

**✅ Completed:** - CLI framework with all commands (``sync``, ``diff``,
``validate``, ``expand``, ``list-templates``) - Comprehensive data
models for all Koji object types (8 CORE_MODELS) - Pydantic validation
with field constraints and proper error handling - Dependency resolution
architecture (Resolver and Solver modules) - Tiered execution system
with automatic splitting for cross-dependencies - Comprehensive unit
test coverage (349 tests across 17 test files) - Template expansion and
YAML processing - Processor module with state machine for
synchronization - Change tracking and reporting system - Multicall
integration for efficient Koji operations

**🚧 In Progress:** - CLI command body implementation (``sync`` and
``validate`` commands are stubs) - CLI testing (currently missing test
coverage for CLI module)

**📋 Next Steps:** - Implement ``sync`` and ``validate`` command bodies
- Add CLI testing (currently 0% test coverage for CLI module) -
Performance optimization and error handling improvements

Overview
--------

koji-habitude is a configuration management tool for
`Koji <https://pagure.io/koji>`__ build systems. It provides a
declarative approach to managing koji objects through YAML templates and
data files, with intelligent dependency resolution and tiered execution.

The tool synchronizes local koji data expectations with a hub instance,
allowing you to: - Define koji objects (tags, external repos, users,
targets, hosts, groups) in YAML - Use Jinja2 templates for dynamic
configuration generation - Automatically resolve dependencies between
objects (tag inheritance) - Preview template expansion results with the
``expand`` command - Apply changes in the correct order through tiered
execution - Validate configurations offline before deployment

This project is an offshoot of
`koji-box <https://github.com/obriencj/koji-box>`__, fulfilling the need
for populating a boxed koji instance with a bunch of tags and targets.
However it is being written such that it can be used with any koji
instance, in the hopes that it may bring joy into the lives of those
trying to keep projects packagers happy.

CLI
---

koji-habitude is built using
`Click <https://click.palletsprojects.com/>`__ and provides five main
commands:

**✅ Fully Implemented:** - ``list-templates`` - List and inspect
available templates - ``expand`` - Expand templates and output final
YAML

**🚧 Command Structure Only (stubs):** - ``sync`` - Synchronize with
Koji hub - ``validate`` - Validate configuration files - ``diff`` - Show
differences (alias for ``sync --dry-run``)

Synchronize with Koji Hub
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   koji-habitude sync [OPTIONS] DATA [DATA...]

**⚠️ Note**: This command is currently a stub and not yet implemented.

**Options:** - ``DATA``: directories or files to work with -
``--templates PATH``: location to find templates that are not available
in ``DATA`` - ``--profile PROFILE``: Koji profile to use for connection
(optional) - ``--offline``: Run in offline mode (no koji connection) -
``--dry-run``: Show what would be done without making changes

.. code:: bash

   koji-habitude diff [OPTIONS] DATA [DATA...]

**⚠️ Note**: This command is currently a stub and not yet implemented.

A convenience alias for ``koji-habitude sync --dry-run``

List Available Templates
~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   koji-habitude list-templates [OPTIONS] PATH [PATH...]

**✅ Fully Implemented**: Shows all templates found in the given
locations with their configuration details.

**Options:** - ``PATH``: directories containing template files -
``--templates PATH``: load only templates from the given paths -
``--yaml``: show expanded templates as YAML - ``--full``: show full
template details including file locations and trace information -
``--select NAME``: select specific templates by name

Validate Configuration
~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   koji-habitude validate [OPTIONS] DATA [DATA...]

**⚠️ Note**: This command is currently a stub and not yet implemented.

Validates templates and data files without connecting to koji, checking
for: - Template syntax and structure - Circular dependencies - Missing
dependencies - Data consistency

Expand Templates and Data
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   koji-habitude expand [OPTIONS] DATA [DATA...]

**✅ Fully Implemented**: Expands templates and data files into final
YAML output.

**Options:** - ``DATA``: directories or files to work with -
``--templates PATH``: location to find templates that are not available
in ``DATA``

This command loads templates from the specified locations, processes the
data files through template expansion, and outputs the final YAML
content to stdout. Useful for previewing the results of template
expansion before applying changes.

YAML Format
-----------

The yaml files can be single or multi-document. Documents are processed
in-order. Each document has ‘type’ key, which indicates the document
type. The default available types are ‘template’, ‘tag’, ‘target’,
‘user’, ‘group’, ‘host’, and ‘external-repo’. Templates define new
types, based on the name of the template.

Templates
---------

Templates use `Jinja2 <https://jinja.palletsprojects.com/>`__ for
dynamic content generation. Each template is defined in YAML with the
following structure:

.. code:: yaml

   ---
   type: template
   name: my-template
   content: |
     ---
     type: tag
     name: {{ name }}
     inheritance:
       {% for parent in parents %}
       - parent: {{ parent }}
         priority: {{ loop.index * 10 }}
       {% endfor %}
   schema:
     # Optional schema validation (future feature)

Templates can also reference external Jinja2 files:

.. code:: yaml

   ---
   type: template
   name: my-template
   file: my-template.j2
   schema:
     # Optional schema validation

Template Expansion
~~~~~~~~~~~~~~~~~~

When processing data files, objects with ``type`` matching a template
name trigger template expansion:

.. code:: yaml

   ---
   type: my-template
   name: fedora-42-build
   parents:
     - fedora-42-base
     - fedora-42-updates

This expands into the final koji objects through recursive template
processing.

Types
-----

koji-habitude supports all core Koji object types with fully implemented
Pydantic models:

Core Types
~~~~~~~~~~

- **``tag``**: Build tags with inheritance chains and external
  repositories
- **``external-repo``**: External package repositories with URL
  validation
- **``user``**: Koji users and permissions with group membership
- **``target``**: Build targets linking build and destination tags
- **``host``**: Build hosts and their configurations with architecture
  support
- **``group``**: Package groups and their memberships
- **``channel``**: Build channels with host assignments
- **``permission``**: User permission definitions

Dependencies
~~~~~~~~~~~~

The system automatically detects dependencies between objects using the
implemented ``dependency_keys()`` methods:

- **Tags** depend on parent tags and external repositories
- **Targets** depend on build and destination tags
- **Groups** depend on users and permissions
- **Users** depend on groups and permissions
- **Hosts** depend on channels
- **Channels** depend on hosts
- **External repos** and **permissions** have no dependencies

Dependency Resolution
~~~~~~~~~~~~~~~~~~~~~

The implemented Resolver and Solver modules provide intelligent
dependency resolution:

1. **Resolver Module**: Handles external dependencies and creates
   placeholders for missing objects
2. **Solver Module**: Creates tiered execution plans with priority-based
   ordering
3. **Automatic Splitting**: Cross-tier dependencies are resolved through
   object splitting
4. **Tiered Execution**: Objects are processed in dependency-resolved
   tiers to ensure proper ordering

The system handles complex dependency scenarios including circular
references and cross-tier dependencies through sophisticated graph
algorithms.

Architecture
------------

koji-habitude implements a sophisticated architecture for managing koji
object synchronization:

Core Components
~~~~~~~~~~~~~~~

- **Template System**: Jinja2-based template expansion with recursive
  processing
- **Dependency Resolution**: Resolver and Solver modules for intelligent
  ordering
- **Processor Module**: State machine-driven synchronization engine
- **Change Tracking**: Comprehensive reporting of modifications and
  differences

Processor Module
~~~~~~~~~~~~~~~~

The ``Processor`` class is the core synchronization engine that manages
the read/compare/apply cycle:

- **State Machine**: ``ProcessorState`` enum manages processing phases
  (READY_CHUNK → READY_READ → READY_COMPARE → READY_APPLY)
- **Chunking**: Processes objects in configurable chunks for memory
  efficiency
- **Multicall Integration**: Uses koji’s multicall API for efficient
  batch operations
- **Change Tracking**: ``ChangeReport`` system tracks all modifications
- **Dry-Run Support**: ``DiffOnlyProcessor`` for previewing changes
  without applying them

Data Flow
~~~~~~~~~

1. **Loading**: YAML files loaded via ``MultiLoader`` and ``YAMLLoader``
2. **Expansion**: Templates expanded recursively through
   ``ExpanderNamespace``
3. **Resolution**: Dependencies resolved via ``Resolver`` and ``Solver``
4. **Processing**: Objects processed in dependency order via
   ``Processor``
5. **Synchronization**: Changes applied to koji hub with multicall
   optimization

Requirements
------------

- `Python <https://python.org>`__ 3.8+
- `Koji <https://pagure.io/koji>`__ client libraries
- `Click <https://click.palletsprojects.com/>`__ for CLI
- `PyYAML <https://pyyaml.org/>`__ for configuration parsing
- `Jinja2 <https://jinja.palletsprojects.com/>`__ for template
  processing
- `Pydantic <https://pydantic-docs.helpmanual.io/>`__ for data
  validation

Installation
------------

.. code:: bash

   pip install -e .

Contact
-------

**Author**: Christopher O’Brien obriencj@gmail.com

**Original Git Repo**: https://github.com/obriencj/koji-habitude

AI Assistance Disclaimer
------------------------

This project was developed with assistance from
`Claude <https://claude.ai>`__ (Claude 3.5 Sonnet) via `Cursor
IDE <https://cursor.com>`__. The AI assistant helped with bootstrapping,
unit tests, and documentation while following the project’s functional
programming principles and coding standards.

See `VIBE.md <VIBE.md>`__ for a very human blurb about how much of an
impact this has had on various files.

License
-------

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
Public License for more details.

You should have received a copy of the GNU General Public License along
with this program. If not, see https://www.gnu.org/licenses/.

.. raw:: html

   <!-- The end -->

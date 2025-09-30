koji-habitude
=============

**🚧 WORK IN PROGRESS 🚧**

This project is *not* production ready. It’s coming along fast, but
there are challenges cropping up all of the time. Until this project has
a version of 1.0, do not attempt to use it with a production Koji
instance.

However, if you have a test instance you want to try it on, give that a
go and let me know!

Overview
--------

koji-habitude is a configuration management tool for
`Koji <https://pagure.io/koji>`__ build systems. It provides a
declarative approach to managing koji objects through YAML templates and
data files, with intelligent dependency resolution and tiered execution.

**Key Features:** - Define koji objects (tags, external repos, users,
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

Current Status
--------------

**Implemented:** - Complete CLI framework with all core commands
(``sync``, ``diff``, ``expand``, ``list-templates``) - All Koji object
types (8 CORE_MODELS) with Pydantic validation - Dependency resolution
architecture (Resolver and Solver modules) - Processor module with state
machine and multicall integration - Comprehensive unit testing (360
tests, 74% coverage) - Template expansion and change tracking system

**Next Steps:** - CLI testing coverage improvements - Integration
testing on a real koji instance - Performance optimization and error
handling improvements

CLI Commands
------------

koji-habitude is built using
`Click <https://click.palletsprojects.com/>`__ and provides four main
commands:

Core Commands
~~~~~~~~~~~~~

**``sync``** - Synchronize with Koji hub

.. code:: bash

   koji-habitude sync [OPTIONS] DATA [DATA...]

- Loads templates and data files with dependency resolution
- Processes objects in dependency-resolved order using Solver
- Fetches current state from koji using multicall optimization
- Applies changes in correct order with error handling

**``diff``** - Show differences (dry-run)

.. code:: bash

   koji-habitude diff [OPTIONS] DATA [DATA...]

- Same processing as sync command but skips write operations
- Uses DiffOnlyProcessor to prevent actual changes
- Provides detailed change analysis and dependency reporting

**``expand``** - Expand templates and output final YAML

.. code:: bash

   koji-habitude expand [OPTIONS] DATA [DATA...]

- Loads templates and processes data files through template expansion
- Outputs final YAML content to stdout
- Use ``--validate`` flag for offline validation

**``list-templates``** - List and inspect available templates

.. code:: bash

   koji-habitude list-templates [OPTIONS] PATH [PATH...]

- Lists available templates with options for YAML output and full
  details
- Use ``--select NAME`` to filter specific templates

Common Options
~~~~~~~~~~~~~~

- ``DATA``: directories or files to work with
- ``--templates PATH``: location to find templates not in ``DATA``
- ``--profile PROFILE``: Koji profile to use (default: ‘koji’)
- ``--show-unchanged``: Show objects that don’t need changes

YAML Format & Templates
-----------------------

YAML files can be single or multi-document, processed in-order. Each
document has a ‘type’ key indicating the document type. Default types
are ‘template’, ‘tag’, ‘target’, ‘user’, ‘group’, ‘host’, and
‘external-repo’. Templates define new types based on their name.

Template System
~~~~~~~~~~~~~~~

Templates use `Jinja2 <https://jinja.palletsprojects.com/>`__ for
dynamic content generation:

**Inline Template:**

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
       - name: {{ parent }}
         priority: {{ loop.index * 10 }}
       {% endfor %}

**External Template:**

.. code:: yaml

   ---
   type: template
   name: my-template
   file: my-template.j2

**Template Usage:**

.. code:: yaml

   ---
   type: my-template
   name: fedora-42-build
   parents:
     - fedora-42-base
     - fedora-42-updates

When processing data files, objects with ``type`` matching a template
name trigger template expansion, creating final koji objects through
recursive processing.

Supported Types & Architecture
------------------------------

Core Koji Object Types
~~~~~~~~~~~~~~~~~~~~~~

koji-habitude supports all core Koji object types with fully implemented
Pydantic models:

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

Dependency Resolution
~~~~~~~~~~~~~~~~~~~~~

The system automatically detects dependencies between objects and
provides intelligent resolution:

- **Resolver Module**: Handles external dependencies and creates
  placeholders for missing objects
- **Solver Module**: Creates tiered execution plans with priority-based
  ordering
- **Automatic Splitting**: Cross-tier dependencies are resolved through
  object splitting
- **Tiered Execution**: Objects are processed in dependency-resolved
  tiers to ensure proper ordering

Architecture Components
~~~~~~~~~~~~~~~~~~~~~~~

- **Template System**: Jinja2-based template expansion with recursive
  processing
- **Processor Module**: State machine-driven synchronization engine with
  multicall integration
- **Change Tracking**: ``ChangeReport`` system tracks all modifications
  with detailed explanations
- **Dry-Run Support**: ``DiffOnlyProcessor`` for previewing changes
  without applying them

**Data Flow**: YAML files → Template expansion → Dependency resolution →
Tiered processing

Requirements & Installation
---------------------------

**Requirements:** - Python 3.8+ - Koji client libraries, Click, PyYAML,
Jinja2, Pydantic

**Installation:**

.. code:: bash

   pip install -e .

Contact & License
-----------------

**Author**: Christopher O’Brien <obriencj@gmail.com

**Repository**: https://github.com/obriencj/koji-habitude

**AI Assistance**: This project was developed with assistance from
`Claude <https://claude.ai>`__ (Claude 3.5 Sonnet) via `Cursor
IDE <https://cursor.com>`__. See `VIBE.md <VIBE.md>`__ for details.

**License**: GNU General Public License v3 or later. See
https://www.gnu.org/licenses/ for details.

.. raw:: html

   <!-- The end -->

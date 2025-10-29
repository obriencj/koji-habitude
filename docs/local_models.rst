Local Object Models
===================

Overview
--------

koji-habitude includes a complete set of local object models that represent
koji objects defined in YAML configuration files. These models are validated,
processed, and synchronized with remote Koji instances.

Local models are the primary interface for defining and managing koji objects
through YAML files. They support dependency resolution, validation, and
automatic synchronization with remote koji instances.

Architecture
------------

Local Models
~~~~~~~~~~~~

The following local model types are supported, each with detailed YAML schemas:

- ``Tag`` - Build tags with inheritance chains and external repositories
- ``Target`` - Build targets linking build and destination tags
- ``User`` - Koji users with group membership and permissions
- ``Group`` - Package groups and their memberships
- ``Host`` - Build hosts and their configurations with architecture support
- ``Channel`` - Build channels with host assignments
- ``Permission`` - User permission definitions
- ``ExternalRepo`` - External package repositories with URL validation
- ``ContentGgenerator`` - Content generators with user access control
- ``BuildType`` - Build type definitions (rpm, maven, image, etc.)
- ``ArchiveType`` - Archive type definitions with file extensions and compression

See :doc:`yaml_format` for detailed schemas and field specifications for each type.

Loading from YAML
-----------------

Local models are loaded from YAML files using the loader system:

.. code:: yaml

   ---
   type: tag
   name: fedora-42-build
   arches:
     - x86_64
     - aarch64
   inheritance:
     - parent: fedora-42-base
       priority: 10

The loader system:

1. Reads YAML documents from files
2. Injects ``__file__`` and ``__line__`` metadata
3. Validates structure using Pydantic models
4. Creates ``CoreObject`` instances from validated data

Validation
----------

All local models use Pydantic for validation with the following features:

- **Type Validation**: Automatic type checking and conversion
- **Field Constraints**: Min/max values, string patterns, list lengths
- **Required Fields**: Automatic validation of required fields
- **Aliases**: Support for field aliases (e.g., ``build-tag`` vs ``build_tag``)
- **Custom Validators**: Complex validation logic for koji-specific rules

Validation occurs during model instantiation, providing immediate feedback
on configuration errors with detailed error messages including file and line
number information.

Dependency Resolution
---------------------

Local models declare dependencies through the ``dependency_keys()`` method,
which returns a sequence of ``(typename, name)`` tuples. The resolver system:

1. Collects all dependencies from local models
2. Organizes dependencies into tiers based on dependency relationships
3. Ensures objects are processed in the correct order
4. Identifies missing dependencies (phantoms) and circular dependencies

This enables safe, ordered processing of koji objects where child objects
are created before their parents.

Processing and Synchronization
------------------------------

Local models integrate with the workflow system for synchronization:

1. **Loading**: YAML files are loaded and validated into local models
2. **Template Expansion**: Templates are expanded, generating additional local models
3. **Resolution**: Dependencies are resolved and objects are organized into tiers
4. **Comparison**: Local models are compared with remote state to identify changes
5. **Application**: Changes are applied to the Koji instance in dependency order

The ``change_report()`` method on each local model generates a ``ChangeReport``
describing what changes need to be made to synchronize with the remote instance.

Example Usage
-------------

Define objects in YAML:

.. code:: yaml

   ---
   type: tag
   name: fedora-42-base
   arches:
     - x86_64
     - aarch64

   ---
   type: tag
   name: fedora-42-build
   arches:
     - x86_64
     - aarch64
   inheritance:
     - parent: fedora-42-base
       priority: 10

   ---
   type: target
   name: fedora-42
   build-tag: fedora-42-build
   dest-tag: fedora-42-dest

Process with koji-habitude:

.. code:: bash

   koji-habitude compare data/ --templates templates/
   koji-habitude apply data/ --templates templates/

The system validates, resolves dependencies, compares with remote state,
and applies changes in the correct order.

Technical Reference
-------------------

For developers: Local models are implemented by classes inheriting from
``CoreObject`` in the :mod:`koji_habitude.models` package. Each model type
has a corresponding class (e.g., ``Tag``, ``Target``, ``User``) that combines
a ``*Model`` class (shared with remote models) with ``CoreObject``.

Local models use the same base classes as remote models (through ``CoreModel``),
ensuring consistency in data structures and validation rules across both
representations.

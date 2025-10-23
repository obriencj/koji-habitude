Remote Object Models
====================

Overview
--------

koji-habitude includes a complete set of remote object models that represent
the current state of objects in a Koji instance. These models are used for
comparison, fetching, and synchronization operations.

The remote models provide a clean interface for working with data retrieved
from the Koji API, enabling bidirectional synchronization between local
configuration files and the remote Koji instance.

Architecture
-----------

Remote Models
~~~~~~~~~~~~

Each core model has a corresponding remote model that inherits from both
the shared model and the ``RemoteObject`` base class:

- ``RemoteTag`` - Remote tag objects from Koji API
- ``RemoteUser`` - Remote user objects with permissions
- ``RemoteTarget`` - Remote build targets
- ``RemoteHost`` - Remote build hosts
- ``RemoteGroup`` - Remote package groups
- ``RemoteChannel`` - Remote build channels
- ``RemotePermission`` - Remote permission definitions
- ``RemoteExternalRepo`` - Remote external repositories
- ``RemoteContentGenerator`` - Remote content generators
- ``RemoteBuildType`` - Remote build type definitions
- ``RemoteArchiveType`` - Remote archive type definitions

Base Classes
~~~~~~~~~~~

- ``RemoteObject`` - Base class for all remote models
  - Includes ``koji_id`` field for Koji database ID
  - Provides ``from_koji()`` class method for API data conversion
  - Implements ``to_dict()`` for YAML serialization
  - Excludes ``koji_id`` from serialized output by default

- ``CoreObject`` - Base class for local models with full functionality
  - Inherits from ``LocalMixin`` and ``ResolvableMixin``
  - Provides dependency resolution and processing capabilities
  - Includes ``remote()`` method to access remote state

- ``CoreModel`` - Shared base for both local and remote models
  - Contains common fields and validation logic
  - Enables consistent data structures across local and remote representations

Mixin Classes
~~~~~~~~~~~~

- ``IdentifiableMixin`` - Provides object identification and key generation
- ``LocalMixin`` - Handles local data storage and YAML loading
- ``ResolvableMixin`` - Manages remote state loading and comparison

Usage
-----

The fetch command uses these remote models to pull current state from Koji:

.. code:: bash

   koji-habitude fetch --show-unchanged data/ > remote-state.yaml

This outputs YAML documents representing the remote state of all objects
that exist in the Koji instance.

Fetch Command Options
~~~~~~~~~~~~~~~~~~~~~

- ``--show-unchanged`` - Include all objects, not just those that differ
- ``--include-defaults`` - Include default values in output
- ``--output PATH`` - Write to file instead of stdout
- ``--profile PROFILE`` - Use specific Koji profile
- ``--templates PATH`` - Additional template locations

Example Output
~~~~~~~~~~~~~~

The fetch command produces YAML in the same format as local configuration
files, making it easy to compare or use as a starting point for new
configurations:

.. code:: yaml

   ---
   type: tag
   name: fedora-42-build
   inheritance:
     - name: fedora-42-base
       priority: 10
   external_repos:
     - name: fedora-42-updates
       url: https://mirrors.fedoraproject.org/metalink?repo=updates-released-f42&arch=x86_64
   packages:
     - name: kernel
       owner: kernel-maint
       block: false

Integration with Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~

Remote models integrate seamlessly with the existing workflow system:

1. **Comparison**: ``CompareWorkflow`` uses remote models to identify differences
2. **Change Detection**: ``ChangeReport`` tracks modifications between local and remote
3. **Synchronization**: ``Processor`` applies changes based on remote state analysis

The remote models enable the system to provide accurate change detection
and safe synchronization operations.

API Integration
~~~~~~~~~~~~~~~

Remote models use enhanced multicall integration with the new ``VirtualPromise``
system for efficient batch operations:

- **Async Loading**: Multiple remote objects loaded in parallel
- **Promise-based**: Callbacks triggered when API calls complete
- **Error Handling**: Graceful handling of missing or invalid objects
- **Performance**: Reduced API round-trips through batching

This architecture provides a robust foundation for bidirectional
synchronization between local configurations and Koji instances.

# The end.

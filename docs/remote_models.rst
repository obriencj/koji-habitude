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
------------

Remote Models
~~~~~~~~~~~~~

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

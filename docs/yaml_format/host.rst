Host Object Schema
===================

The ``host`` type represents a Koji host object.

Basic Structure
---------------

.. code-block:: yaml

   ---
   type: host
   name: my-host
   # ... host-specific fields

YAML Fields
-----------

Optional Fields
~~~~~~~~~~~~~~~

``arches`` (list of str)
   List of architectures this tag supports (e.g., ['x86_64', 'aarch64'])

``capacity`` (Optional)
   Build capacity for this host

``enabled`` (boolean) - Default: True
   Whether this host is enabled for builds

``description`` (Optional)
   Configuration for description

``channels`` (list of str)
   List of channels this host is assigned to

``exact-channels`` (boolean) - Default: False
   Configuration for exact channels

Examples
--------

Basic Host
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   ---
   type: host
   name: my-host
   arches:
     - x86_64
     - aarch64
   capacity: 2.0
   enabled: true
   channels:
     - default

Validation Rules
----------------

- All field types are automatically validated
- Required fields must be present
- Field constraints are enforced (min/max values, string patterns, etc.)
- Duplicate priorities are not allowed in inheritance or external-repos lists

Dependencies
------------

This object type can depend on other objects. Dependencies are automatically
resolved during processing to ensure proper creation order.

Technical Reference
-------------------

For developers: The ``host`` object is implemented by the
:class:`koji_habitude.models.host.Host` class.


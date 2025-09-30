Host Object Schema
===================

The ``host`` type represents a Koji host object.


Basic Structure
---------------

.. code-block:: yaml

   ---
   type: host
   name: my-host

   # Optional fields

   # List of architectures this host supports
   arches:
     - x86_64
     - aarch64

   # Build capacity for this host
   capacity: 2.0

   # Whether this host is enabled for builds
   enabled: true

   # Description of this host
   description: My build host

   # List of channels this host is assigned to
   channels:
     - default

   # If true, remove any existing channels not listed above
   exact-channels: false


YAML Fields
-----------

Required Fields
~~~~~~~~~~~~~~~

``type`` (str)
   The type of the object, must be ``host``

``name`` (str)
   The name of the host


Optional Fields
~~~~~~~~~~~~~~~

``arches`` (list of str)
   List of architectures this host supports (e.g., ['x86_64', 'aarch64'])

``capacity`` (float)
   Build capacity for this host

``enabled`` (boolean) - Default: True
   Whether this host is enabled for builds

``description`` (str)
   Description of this host

``channels`` (list of str)
   List of channels this host is assigned to

``exact-channels`` (boolean) - Default: False
   If true, remove any existing channels not listed in the channels field


Dependencies
------------

This object type depends on the ``channel`` object type for each channel listed in the
``channels`` field.


Technical Reference
-------------------

For developers: The ``host`` object is implemented by the
:class:`koji_habitude.models.host.Host` class.

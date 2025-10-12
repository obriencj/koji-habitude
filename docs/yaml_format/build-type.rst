Build Type Object Schema
=========================

The ``build-type`` type represents a Koji build type object.


Basic Structure
---------------

.. code-block:: yaml

   ---
   type: build-type
   name: rpm


YAML Fields
-----------

Required Fields
~~~~~~~~~~~~~~~

``type`` (str)
   The type of the object, must be ``build-type``

``name`` (str)
   The name of the build type (e.g., ``rpm``, ``maven``, ``image``, ``win``)


Optional Fields
~~~~~~~~~~~~~~~

This object type has no optional fields.


Dependencies
------------

This object type has no dependencies on other koji-habitude objects.


Examples
--------

Standard Build Types
~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   ---
   type: build-type
   name: rpm

   ---
   type: build-type
   name: maven

   ---
   type: build-type
   name: image

   ---
   type: build-type
   name: win


Notes
-----

Build types define the fundamental categories of builds that Koji can handle.
Once created, build types cannot be modified through the Koji API. Common
build types include:

- ``rpm`` - Traditional RPM package builds
- ``maven`` - Maven artifact builds
- ``image`` - Container/VM image builds
- ``win`` - Windows builds
- ``module`` - Modular builds


Technical Reference
-------------------

For developers: The ``build-type`` object is implemented by the
:class:`koji_habitude.models.build_type.BuildType` class.

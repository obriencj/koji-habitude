Permission Object Schema
=========================

The ``permission`` type represents a Koji permission object.


Basic Structure
---------------

.. code-block:: yaml

   ---
   type: permission
   name: my-permission

   # Optional fields

   # Description of this permission
   description: My permission description


YAML Fields
-----------

Required Fields
~~~~~~~~~~~~~~~

``type`` (str)
   The type of the object, must be ``permission``

``name`` (str)
   The name of the permission


Optional Fields
~~~~~~~~~~~~~~~

``description`` (str)
   Description of this permission


Dependencies
------------

This object type has no dependencies on other koji-habitude objects.


Technical Reference
-------------------

For developers: The ``permission`` object is implemented by the
:class:`koji_habitude.models.permission.Permission` class.

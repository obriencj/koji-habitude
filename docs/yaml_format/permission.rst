Permission Object Schema
=========================

The ``permission`` type represents a Koji permission object.

Basic Structure
---------------

.. code-block:: yaml

   ---
   type: permission
   name: my-permission
   # ... permission-specific fields

YAML Fields
-----------

Optional Fields
~~~~~~~~~~~~~~~

``description`` (Optional)
   Configuration for description

Examples
--------

Basic Permission
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   ---
   type: permission
   name: my-permission

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

For developers: The ``permission`` object is implemented by the
:class:`koji_habitude.models.permission.Permission` class.


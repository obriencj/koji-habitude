Target Object Schema
=====================

The ``target`` type represents a Koji target object.

Basic Structure
---------------

.. code-block:: yaml

   ---
   type: target
   name: my-target
   # ... target-specific fields

YAML Fields
-----------

Required Fields
~~~~~~~~~~~~~~~

``build-tag`` (string)
   Configuration for build tag

Optional Fields
~~~~~~~~~~~~~~~

``dest-tag`` (Optional)
   Configuration for dest tag

Examples
--------

Basic Target
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   ---
   type: target
   name: my-target

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

For developers: The ``target`` object is implemented by the
:class:`koji_habitude.models.target.Target` class.


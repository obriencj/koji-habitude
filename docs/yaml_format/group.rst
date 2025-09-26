Group Object Schema
====================

The ``group`` type represents a Koji group object.

Basic Structure
---------------

.. code-block:: yaml

   ---
   type: group
   name: my-group
   # ... group-specific fields

YAML Fields
-----------

Optional Fields
~~~~~~~~~~~~~~~

``enabled`` (boolean) - Default: True
   Whether this host is enabled for builds

``members`` (list of str)
   List of members in this group

``permissions`` (list of str)
   List of permissions for this group

Examples
--------

Basic Group
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   ---
   type: group
   name: my-group
   enabled: true
   members:
     - user1
     - user2
   permissions:
     - admin
     - build

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

For developers: The ``group`` object is implemented by the
:class:`koji_habitude.models.group.Group` class.


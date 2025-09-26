User Object Schema
===================

The ``user`` type represents a Koji user object.

Basic Structure
---------------

.. code-block:: yaml

   ---
   type: user
   name: my-user
   # ... user-specific fields

YAML Fields
-----------

Optional Fields
~~~~~~~~~~~~~~~

``groups`` (list of str)
   Package groups and their package lists

``exact_groups`` (boolean) - Default: False
   Configuration for exact_groups

``permissions`` (list of str)
   List of permissions for this group

``exact-permissions`` (boolean) - Default: False
   Configuration for exact permissions

``enabled`` (boolean) - Default: True
   Whether this host is enabled for builds

Examples
--------

Basic User
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   ---
   type: user
   name: my-user
   groups:
     my-group:
       - package1
       - package2
   permissions:
     - admin
     - build
   enabled: true

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

For developers: The ``user`` object is implemented by the
:class:`koji_habitude.models.user.User` class.


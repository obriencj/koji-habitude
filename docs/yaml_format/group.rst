Group Object Schema
====================

The ``group`` type represents a Koji group object.


Basic Structure
---------------

.. code-block:: yaml

   ---
   type: group
   name: my-group

   # Optional fields

   # Whether this group is enabled
   enabled: true

   # List of user members in this group
   members:
     - user1
     - user2

   # List of permissions for this group
   permissions:
     - admin
     - build

   # If true, remove any existing members not listed above
   exact-members: false

   # If true, remove any existing permissions not listed above
   exact-permissions: false


YAML Fields
-----------

Required Fields
~~~~~~~~~~~~~~~

``type`` (str)
   The type of the object, must be ``group``

``name`` (str)
   The name of the group


Optional Fields
~~~~~~~~~~~~~~~

``enabled`` (boolean) - Default: True
   Whether this group is enabled

``members`` (list of str)
   List of user members in this group

``permissions`` (list of str)
   List of permissions for this group

``exact-members`` (boolean) - Default: False
   If true, remove any existing members not listed in the members field

``exact-permissions`` (boolean) - Default: False
   If true, remove any existing permissions not listed in the permissions field


Dependencies
------------

This object type depends on the ``user`` object type for each user listed in the
``members`` field and the ``permission`` object type for each permission listed in the
``permissions`` field.


Technical Reference
-------------------

For developers: The ``group`` object is implemented by the
:class:`koji_habitude.models.group.Group` class.

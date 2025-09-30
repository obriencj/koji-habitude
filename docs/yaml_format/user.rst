User Object Schema
===================

The ``user`` type represents a Koji user object.


Basic Structure
---------------

.. code-block:: yaml

   ---
   type: user
   name: my-user

   # Optional fields

   # List of groups this user belongs to
   groups:
     - my-group

   # If true, remove any existing groups not listed above
   exact-groups: false

   # List of permissions for this user
   permissions:
     - admin
     - build

   # If true, remove any existing permissions not listed above
   exact-permissions: false

   # Whether this user is enabled (None means use default)
   enabled: true


YAML Fields
-----------

Required Fields
~~~~~~~~~~~~~~~

``type`` (str)
   The type of the object, must be ``user``

``name`` (str)
   The name of the user


Optional Fields
~~~~~~~~~~~~~~~

``groups`` (list of str)
   List of groups this user belongs to

``exact-groups`` (boolean) - Default: False
   If true, remove any existing groups not listed in the groups field

``permissions`` (list of str)
   List of permissions for this user

``exact-permissions`` (boolean) - Default: False
   If true, remove any existing permissions not listed in the permissions field

``enabled`` (boolean)
   Whether this user is enabled. If not specified, uses the default behavior


Dependencies
------------

This object type depends on the ``group`` object type for each group listed in the
``groups`` field and the ``permission`` object type for each permission listed in the
``permissions`` field.


Technical Reference
-------------------

For developers: The ``user`` object is implemented by the
:class:`koji_habitude.models.user.User` class.

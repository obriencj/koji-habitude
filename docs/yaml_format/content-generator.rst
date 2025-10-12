Content Generator Object Schema
=================================

The ``content-generator`` type represents a Koji content generator object.


Basic Structure
---------------

.. code-block:: yaml

   ---
   type: content-generator
   name: my-cg

   # Optional fields

   # List of users with access to this content generator
   users:
     - user1
     - user2

   # Whether to enforce exact user list (remove unlisted users)
   exact-users: false


YAML Fields
-----------

Required Fields
~~~~~~~~~~~~~~~

``type`` (str)
   The type of the object, must be ``content-generator``

``name`` (str)
   The name of the content generator


Optional Fields
~~~~~~~~~~~~~~~

``users`` (list of str) - Default: []
   List of users who have access to use this content generator for imports

``exact-users`` (boolean) - Default: False
   If true, any existing users with access to this content generator will be
   removed if they are not specified in the ``users`` list. If false (default),
   only adds missing users without removing existing ones.


Dependencies
------------

This object type depends on the ``user`` object type for each user listed in the
``users`` field.


Examples
--------

Basic Content Generator
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   ---
   type: content-generator
   name: osbs
   users:
     - osbs-worker

Content Generator with Multiple Users
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   ---
   type: content-generator
   name: custom-importer
   users:
     - importer-bot
     - admin-user
     - backup-importer
   exact-users: true


Technical Reference
-------------------

For developers: The ``content-generator`` object is implemented by the
:class:`koji_habitude.models.content_generator.ContentGenerator` class.


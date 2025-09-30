Tag Object Schema
==================

The ``tag`` type represents a Koji tag object.


Basic Structure
---------------

.. code-block:: yaml

   ---
   type: tag
   name: my-tag

   # Optional fields

   # Whether the tag is locked (prevents builds and other modifications)
   locked: false

   # Permission required to use this tag
   permission: admin

   # List of architectures this tag supports
   arches:
     - x86_64
     - aarch64

   # Whether Maven support is enabled for this tag
   maven-support: false

   # Whether to include all Maven artifacts in this tag
   maven-include-all: false

   # Additional tag metadata as key-value pairs
   extras:
     description: "My tag description"

   # Package groups and their package lists
   groups:
     my-group:
       - package1
       - package2

   # List of parent tags with their priorities
   inheritance:
     - parent: parent-tag
       priority: 10

   # List of external repositories attached to this tag
   external-repos:
     - name: my-repo
       priority: 100


YAML Fields
-----------

Required Fields
~~~~~~~~~~~~~~~

``type`` (str)
   The type of the object, must be ``tag``

``name`` (str)
   The name of the tag


Optional Fields
~~~~~~~~~~~~~~~

``locked`` (boolean) - Default: False
   Whether the tag is locked (prevents builds and other modifications)

``permission`` (str)
   Permission required to use this tag

``arches`` (list of str)
   List of architectures this tag supports (e.g., ['x86_64', 'aarch64'])

``maven-support`` (boolean) - Default: False
   Whether Maven support is enabled for this tag

``maven-include-all`` (boolean) - Default: False
   Whether to include all Maven artifacts in this tag

``extras`` (dictionary of str to Any)
   Additional tag metadata as key-value pairs

``groups`` (dictionary of str to List)
   Package groups and their package lists

``inheritance`` (list of InheritanceLink)
   List of parent tags with their priorities

``external-repos`` (list of InheritanceLink)
   List of external repositories attached to this tag


Dependencies
------------

This object type depends on the ``tag`` object type for each parent tag listed in the
``inheritance`` field and the ``external-repo`` object type for each external repository listed in the
``external-repos`` field.


Technical Reference
-------------------

For developers: The ``tag`` object is implemented by the
:class:`koji_habitude.models.tag.Tag` class.

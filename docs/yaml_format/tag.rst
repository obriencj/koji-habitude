Tag Object Schema
==================

The ``tag`` type represents a Koji tag object.

Basic Structure
---------------

.. code-block:: yaml

   ---
   type: tag
   name: my-tag
   # ... tag-specific fields

YAML Fields
-----------

Optional Fields
~~~~~~~~~~~~~~~

``locked`` (boolean) - Default: False
   Whether the tag is locked (prevents builds and other modifications)

``permission`` (Optional)
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

Examples
--------

Basic Tag
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   ---
   type: tag
   name: my-tag
   locked: false
   permission: admin
   arches:
     - x86_64
     - aarch64
   maven-support: false
   maven-include-all: false
   extras:
     description: "My tag description"
   groups:
     my-group:
       - package1
       - package2
   inheritance:
     - parent: parent-tag
       priority: 10
   external-repos:
     - name: my-repo
       priority: 100

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

For developers: The ``tag`` object is implemented by the
:class:`koji_habitude.models.tag.Tag` class.


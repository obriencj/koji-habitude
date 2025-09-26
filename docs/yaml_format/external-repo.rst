External-Repo Object Schema
============================

The ``external-repo`` type represents a Koji external repo object.

Basic Structure
---------------

.. code-block:: yaml

   ---
   type: external-repo
   name: my-external-repo
   # ... external-repo-specific fields

YAML Fields
-----------

Required Fields
~~~~~~~~~~~~~~~

``url`` (string)
   URL for this external repository

Examples
--------

Basic External-Repo
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   ---
   type: external-repo
   name: my-external-repo
   url: https://example.com/repo/

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

For developers: The ``external-repo`` object is implemented by the
:class:`koji_habitude.models.external_repo.ExternalRepo` class.


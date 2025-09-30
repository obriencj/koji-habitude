External-Repo Object Schema
============================

The ``external-repo`` type represents a Koji external repo object.


Basic Structure
---------------

.. code-block:: yaml

   ---
   type: external-repo
   name: my-external-repo

   # Required fields

   # URL for this external repository (must start with http:// or https://)
   url: https://example.com/repo/


YAML Fields
-----------

Required Fields
~~~~~~~~~~~~~~~

``type`` (str)
   The type of the object, must be ``external-repo``

``name`` (str)
   The name of the external repository

``url`` (str)
   URL for this external repository. Must start with ``http://`` or ``https://``


Dependencies
------------

This object type has no dependencies on other koji-habitude objects.


Technical Reference
-------------------

For developers: The ``external-repo`` object is implemented by the
:class:`koji_habitude.models.external_repo.ExternalRepo` class.

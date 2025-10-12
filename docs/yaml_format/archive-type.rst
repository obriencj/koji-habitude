Archive Type Object Schema
===========================

The ``archive-type`` type represents a Koji archive type object.


Basic Structure
---------------

.. code-block:: yaml

   ---
   type: archive-type
   name: jar
   extensions:
     - jar

   # Optional fields

   # Description of the archive type
   description: Java Archive

   # Compression type (tar or zip)
   compression-type: zip


YAML Fields
-----------

Required Fields
~~~~~~~~~~~~~~~

``type`` (str)
   The type of the object, must be ``archive-type``

``name`` (str)
   The name of the archive type

``extensions`` (list of str)
   List of file extensions associated with this archive type. Must contain at
   least one extension. Leading dots are automatically stripped (e.g., ``.jar``
   becomes ``jar``). Duplicate extensions are automatically removed.


Optional Fields
~~~~~~~~~~~~~~~

``description`` (str) - Default: ""
   Description of this archive type

``compression-type`` (Literal['tar', 'zip']) - Default: None
   The compression type for this archive format. Valid values are ``tar`` or
   ``zip``. If not specified, the archive type has no associated compression.


Dependencies
------------

This object type has no dependencies on other koji-habitude objects.


Extension Validation
--------------------

The ``extensions`` field has special validation:

1. **Leading Dot Removal**: Extensions like ``.jar`` are automatically converted
   to ``jar``
2. **Deduplication**: Duplicate extensions (including after dot removal) are
   automatically removed
3. **Minimum Length**: At least one extension must be specified


Examples
--------

Simple Archive Type
~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   ---
   type: archive-type
   name: jar
   extensions:
     - jar


Archive Type with Description
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   ---
   type: archive-type
   name: war
   extensions:
     - war
   description: Web Application Archive


Archive Type with Compression
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   ---
   type: archive-type
   name: tar
   extensions:
     - tar
   description: TAR archive
   compression-type: tar


Archive Type with Multiple Extensions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   ---
   type: archive-type
   name: tarball
   extensions:
     - tar.gz
     - tgz
     - tar.bz2
     - tbz2
   description: Compressed TAR archives
   compression-type: tar


Extensions with Leading Dots (Auto-stripped)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   ---
   type: archive-type
   name: java-archives
   extensions:
     - .jar    # Becomes 'jar'
     - .war    # Becomes 'war'
     - .ear    # Becomes 'ear'
   description: Java archive formats


Notes
-----

Archive types define file formats that Koji recognizes for build artifacts.
Once created, archive types cannot be modified through the Koji API (see
`Koji Issue #4478 <https://pagure.io/koji/issue/4478>`_).

Common archive types include:

- Java artifacts (jar, war, ear)
- Compressed archives (tar, zip)
- Python packages (whl)
- Ruby gems (gem)
- Container images (docker, oci)


Technical Reference
-------------------

For developers: The ``archive-type`` object is implemented by the
:class:`koji_habitude.models.archive_type.ArchiveType` class.

Multi Type Schema
=================

The ``multi`` type is a special macro template that expands a single document
containing key-value pairs into multiple YAML documents. This feature exists
primarily to enable the use of YAML anchors across many objects, as YAML
specification does not allow anchors to be shared between separate documents.


Basic Structure
---------------

.. code-block:: yaml

   ---
   type: multi

   # Keys starting with 'x-' or '_' are ignored and can be used for
   # metadata, extension fields, or YAML anchors
   x-some-value: &some-value lalala
   x-common-config: &common-config
     setting1: value1
     setting2: value2

   # Each key-value pair where the value is a dictionary becomes a
   # separate YAML document
   alma-linux-10-build:
     type: tag
     extra-values:
       some: *some-value
       config: *common-config

   alma-linux-9-build:
     type: tag
     extra-values:
       some: *some-value
       config: *common-config

   alma-linux-10-candidate:
     type: target
     name: alma-linux-10-candidate
     build-tag: alma-linux-10-build

This expands to three separate documents:

.. code-block:: yaml

   ---
   type: tag
   name: alma-linux-10-build
   extra-values:
     some: lalala
     config:
       setting1: value1
       setting2: value2
   ---
   type: tag
   name: alma-linux-9-build
   extra-values:
     some: lalala
     config:
       setting1: value1
       setting2: value2
   ---
   type: target
   name: alma-linux-10-candidate
   build-tag: alma-linux-10-build


YAML Fields
-----------

Required Fields
~~~~~~~~~~~~~~~

``type`` (str)
   The type of the object, must be ``multi``


Special Fields
~~~~~~~~~~~~~~~

Keys starting with ``_`` or ``x-``
   These keys are ignored during expansion and can be used for:

   - **YAML Anchors**: Define anchors (``&anchor-name``) that can be
     referenced (``*anchor-name``) by all objects in the multi document
   - **Metadata**: Store metadata or extension fields that should not
     become separate documents
   - **Shared Configuration**: Define common values that multiple objects
     can reference

   Example:

   .. code-block:: yaml

      ---
      type: multi

      x-version: &version "1.0.0"
      x-common-extras: &common-extras
        maintainer: "team@example.com"
        project: "my-project"

      my-tag:
        type: tag
        extras:
          version: *version
          maintainer: *common-extras


Object Entries
~~~~~~~~~~~~~~

Each key-value pair where the value is a dictionary becomes a separate YAML
document. The behavior depends on whether the dictionary has a ``name`` field:

- **If the dictionary has a ``name`` field**: The object uses that name
- **If the dictionary lacks a ``name`` field**: The key becomes the object's
  name (automatically added)

Example with explicit names:

.. code-block:: yaml

   ---
   type: multi

   my-tag:
     type: tag
     name: explicit-tag-name  # Uses this name

   another-tag:
     type: tag
     # No name field, so 'another-tag' becomes the name

This expands to:

.. code-block:: yaml

   ---
   type: tag
   name: explicit-tag-name
   ---
   type: tag
   name: another-tag


Expansion Rules
---------------

1. **Key Filtering**: Keys starting with ``_`` or ``x-`` are skipped and do
   not generate documents

2. **Empty Values**: Keys with empty or falsy values are skipped

3. **Non-Dictionary Values**: Keys with non-dictionary values are logged as
   debug messages and skipped

4. **Name Assignment**: If a dictionary value doesn't have a ``name`` field,
   the key is automatically assigned as the ``name``

5. **Trace Information**: Each generated document includes trace information
   indicating it came from a ``multi`` expansion


Use Cases
---------

**Shared YAML Anchors**
   The primary use case is to share YAML anchors across multiple objects.
   Since YAML anchors cannot be shared between separate documents, the
   ``multi`` type allows you to define anchors once and reference them in
   multiple objects:

   .. code-block:: yaml

      ---
      type: multi

      x-common-arches: &arches
        - x86_64
        - aarch64

      tag1:
        type: tag
        arches: *arches

      tag2:
        type: tag
        arches: *arches

**Related Objects**
   Group related objects that share configuration patterns or need to
   reference common values:

   .. code-block:: yaml

      ---
      type: multi

      x-base-config: &base-config
        permission: admin
        locked: false

      build-tag:
        type: tag
        <<: *base-config

      dest-tag:
        type: tag
        <<: *base-config

**Template Data Sharing**
   Provide shared template data that multiple objects need to reference
   without duplicating the data:

   .. code-block:: yaml

      ---
      type: multi

      x-product-info: &product-info
        product: "MyProduct"
        version: "1.0"
        release: "1"

      product-build:
        type: tag
        extras:
          <<: *product-info

      product-candidate:
        type: target
        build-tag: product-build
        extras:
          <<: *product-info


Dependencies
------------

The ``multi`` type itself has no dependencies. However, each object generated
from the multi document will have its own dependencies based on its type. For
example, if a multi document contains tag objects with inheritance links,
those will create dependencies on the parent tags.


Technical Reference
-------------------

For developers: The ``multi`` type is implemented by the
:class:`koji_habitude.templates.MultiTemplate` class, which extends
:class:`koji_habitude.templates.Template`.

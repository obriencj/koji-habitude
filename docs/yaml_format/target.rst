Target Object Schema
=====================

The ``target`` type represents a Koji target object.


Basic Structure
---------------

.. code-block:: yaml

   ---
   type: target
   name: my-target

   # Required fields

   # The build tag for this target
   build-tag: my-build-tag

   # Optional fields

   # The destination tag for this target (defaults to target name if not specified)
   dest-tag: my-dest-tag


YAML Fields
-----------

Required Fields
~~~~~~~~~~~~~~~

``type`` (str)
   The type of the object, must be ``target``

``name`` (str)
   The name of the target

``build-tag`` (str)
   The build tag for this target


Optional Fields
~~~~~~~~~~~~~~~

``dest-tag`` (str)
   The destination tag for this target. If not specified, defaults to the target name


Dependencies
------------

This object type depends on the ``tag`` object type for the ``build-tag`` field and the
``tag`` object type for the ``dest-tag`` field (or the target name if dest-tag is not specified).


Technical Reference
-------------------

For developers: The ``target`` object is implemented by the
:class:`koji_habitude.models.target.Target` class.

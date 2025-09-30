Channel Object Schema
=====================

The ``channel`` type represents a Koji channel object.


Basic Structure
---------------

.. code-block:: yaml

   ---
   type: channel
   name: my-channel

   # Optional fields

   # A short summary of the channel's use
   description: My channel description

   # List of hosts assigned to this channel
   hosts:
     - host1.example.com

   # behavior when applying changes. If true then any
   # existing hosts in this channel will be removed if the
   # are not specified above.
   exact-hosts: true


YAML Fields
-----------

Required Fields
~~~~~~~~~~~~~~~

``type`` (str)
   The type of the object, must be ``channel``

``name`` (str)
   The name of the channel


Optional Fields
~~~~~~~~~~~~~~~

``description`` (Optional)
   Configuration for description

``hosts`` (list of str)
   List of hosts assigned to this channel

``exact-hosts`` (boolean) - Default: False
   Configuration for exact hosts


Dependencies
------------

This object type depends on the ``host`` object type for each host listed in the
``hosts`` field.


Technical Reference
-------------------

For developers: The ``channel`` object is implemented by the
:class:`koji_habitude.models.channel.Channel` class.

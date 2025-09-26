Channel Object Schema
======================

The ``channel`` type represents a Koji channel object.

Basic Structure
---------------

.. code-block:: yaml

   ---
   type: channel
   name: my-channel
   # ... channel-specific fields

YAML Fields
-----------

Optional Fields
~~~~~~~~~~~~~~~

``description`` (Optional)
   Configuration for description

``hosts`` (list of str)
   List of hosts assigned to this channel

``exact-hosts`` (boolean) - Default: False
   Configuration for exact hosts

Examples
--------

Basic Channel
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   ---
   type: channel
   name: my-channel
   hosts:
     - buildhost1.example.com

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

For developers: The ``channel`` object is implemented by the
:class:`koji_habitude.models.channel.Channel` class.


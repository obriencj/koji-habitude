Template Object Schema
======================

The ``template`` type allows you to define custom object types using Jinja2 templating.
Templates can optionally define data models for validation and provide type-safe access
to template data.


Basic Structure
---------------

Templates can be defined with either inline content or an external file:

**Inline Template:**

.. code-block:: yaml

   ---
   type: template
   name: my-template
   content: |
     ---
     type: tag
     name: {{ name }}
     arches:
       {% for arch in arches %}
       - {{ arch }}
       {% endfor %}

**External Template File:**

.. code-block:: yaml

   ---
   type: template
   name: my-template
   file: my-template.j2


Template Expansion
------------------

When processing data files, objects with ``type`` matching a template name
trigger template expansion:

.. code-block:: yaml

   ---
   type: my-template
   name: fedora-42-build
   arches:
     - x86_64
     - aarch64

This expands into the final koji objects through recursive template processing.
Template calls inherit metadata (``__file__``, ``__line__``) and maintain a
trace chain (``__trace__``) showing the expansion path.


Model Definitions
-----------------

Templates can define Pydantic models for data validation and type-safe access.
When a model is defined, input data is validated against the model schema before
template rendering, and the validated model instance is made available in the template.

Basic Model Structure
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   ---
   type: template
   name: validated-template
   content: |
     ---
     type: tag
     name: {{ TagModel.name }}
     arches: {{ TagModel.arches | join(', ') }}
   model:
     name: TagModel
     fields:
       name:
         type: string
       arches:
         type: array
         array_item_type:
           type: string

The model instance is accessible in templates using the model name (e.g., ``{{ TagModel.name }}``).
The original unvalidated data is still available as ``{{ _data.field }}``.


Field Types
~~~~~~~~~~~

The following field types are supported:

Basic Types
^^^^^^^^^^^

- ``string`` or ``str``: Text values (maps to Python ``str``)
- ``integer`` or ``int``: Integer values (maps to Python ``int``)
- ``float``: Floating-point values (maps to Python ``float``)
- ``boolean`` or ``bool``: Boolean values (maps to Python ``bool``)

Example:

.. code-block:: yaml

   model:
     name: ProductModel
     fields:
       product_name:
         type: string
       quantity:
         type: int
       price:
         type: float
       active:
         type: bool

Array Types
^^^^^^^^^^^

Arrays can hold any type of data. Use ``array_item_type`` to specify typed arrays:

.. code-block:: yaml

   model:
     name: OrderModel
     fields:
       items:
         type: array
         array_item_type:
           type: string
       quantities:
         type: array
         array_item_type:
           type: int

Without ``array_item_type``, arrays accept mixed types (any value).

Object Types
^^^^^^^^^^^^

Objects define nested structures with named fields:

.. code-block:: yaml

   model:
     name: ConfigModel
     fields:
       metadata:
         type: object
         object_fields:
           author:
             type: string
           version:
             type: int
           description:
             type: string
         object_type_name: Metadata

Nested objects can be accessed in templates: ``{{ ConfigModel.metadata.author }}``.

Enum Types
^^^^^^^^^^

Enums restrict values to a specific set. The validation section must include ``enum``
with the allowed values:

.. code-block:: yaml

   model:
     name: StatusModel
     fields:
       status:
         type: enum
         validation:
           enum:
             - pending
             - active
             - completed

Enum values are accessible in templates. Access the string value via ``.value`` attribute
if needed: ``{{ StatusModel.status.value }}``.


Field Metadata
~~~~~~~~~~~~~~~

Fields support several metadata options:

Required Fields
^^^^^^^^^^^^^^^

By default, all fields are required. Set ``required: false`` to make a field optional:

.. code-block:: yaml

   model:
     name: OptionalModel
     fields:
       required_field:
         type: string
         required: true
       optional_field:
         type: string
         required: false

Default Values
^^^^^^^^^^^^^^

Default values are set using the ``default`` field:

.. code-block:: yaml

   model:
     name: DefaultModel
     fields:
       name:
         type: string
       count:
         type: int
         default: 0
       enabled:
         type: bool
         default: true

Defaults are validated and type-converted to match the field type.

Field Aliases
^^^^^^^^^^^^^

Use ``alias`` to accept data under a different name while accessing it by the field name:

.. code-block:: yaml

   model:
     name: AliasModel
     fields:
       display_name:
         type: string
         alias: name

Input can use either ``display_name`` or ``name``, but access is via ``{{ AliasModel.display_name }}``.

Descriptions
^^^^^^^^^^^^

Add documentation with the ``description`` field:

.. code-block:: yaml

   model:
     name: DocumentedModel
     fields:
       title:
         type: string
         description: "The title of the item"
       count:
         type: int
         description: "Number of items (must be positive)"


Validation Rules
~~~~~~~~~~~~~~~~

Validation rules enforce constraints on field values. Rules are specified in the
``validation`` section of a field definition:

String Validation
^^^^^^^^^^^^^^^^^

- **``min-length``** (int): Minimum string length
- **``max-length``** (int): Maximum string length
- **``regex``** (str): Regular expression pattern to match

.. code-block:: yaml

   model:
     name: ValidatedStringModel
     fields:
       code:
         type: string
         validation:
           min-length: 3
           max-length: 10
       email:
         type: string
         validation:
           regex: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"

Numeric Validation
^^^^^^^^^^^^^^^^^^

- **``min-value``** (float): Minimum numeric value (inclusive)
- **``max-value``** (float): Maximum numeric value (inclusive)

.. code-block:: yaml

   model:
     name: ValidatedIntModel
     fields:
       score:
         type: int
         validation:
           min-value: 0
           max-value: 100
       percentage:
         type: float
         validation:
           min-value: 0.0
           max-value: 100.0

Enum Validation
^^^^^^^^^^^^^^^

- **``enum``** (list): List of allowed values

.. code-block:: yaml

   model:
     name: EnumModel
     fields:
       status:
         type: enum
         validation:
           enum:
             - pending
             - in-progress
             - done

Validation runs during template rendering. Invalid data raises a ``ValidationError``
with detailed error messages.


Template Defaults
-----------------

Templates can define default values that merge with call data before validation:

.. code-block:: yaml

   ---
   type: template
   name: defaults-template
   defaults:
     optional: default-optional
     enabled: true
   content: |
     required: {{ Model.required }}
     optional: {{ Model.optional }}
     enabled: {{ Model.enabled }}
   model:
     name: Model
     fields:
       required:
         type: string
       optional:
         type: string
         required: false
       enabled:
         type: bool

Defaults merge with call data, with call data taking precedence. Merged data is
then validated against the model (if defined).


Accessing Model Data in Templates
---------------------------------

When a template defines a model, the validated model instance is available using
the model name:

.. code-block:: yaml

   ---
   type: template
   name: model-access-template
   content: |
     name: {{ ProductModel.name }}
     count: {{ ProductModel.count }}
     price: {{ ProductModel.price }}
   model:
     name: ProductModel
     fields:
       name:
         type: string
       count:
         type: int
       price:
         type: float

Model instance access provides:
- Type-safe property access
- Validated and converted values
- Support for nested objects and arrays
- Jinja2 filter compatibility (e.g., ``{{ ProductModel.count | string }}``)

Original Data Access
~~~~~~~~~~~~~~~~~~~~

The original, unvalidated call data remains available as ``{{ _data }}``:

.. code-block:: yaml

   ---
   type: template
   name: data-preservation-template
   content: |
     model: {{ Model.value }}
     raw: {{ _data.value }}
     extra: {{ _data.extra | default('none') }}
   model:
     name: Model
     fields:
       value:
         type: string

Use ``_data`` when you need access to fields not in the model, or to work with
the raw input before validation.


Complex Examples
----------------

Nested Objects
~~~~~~~~~~~~~~

.. code-block:: yaml

   ---
   type: template
   name: nested-template
   content: |
     author: {{ DocumentModel.config.author }}
     version: {{ DocumentModel.config.version }}
     title: {{ DocumentModel.title }}
   model:
     name: DocumentModel
     fields:
       title:
         type: string
       config:
         type: object
         object_fields:
           author:
             type: string
           version:
             type: int
         object_type_name: Config

Typed Arrays
~~~~~~~~~~~~

.. code-block:: yaml

   ---
   type: template
   name: array-template
   content: |
     name: {{ TagModel.name }}
     arches:
     {% for arch in TagModel.arches %}
       - {{ arch }}
     {% endfor %}
   model:
     name: TagModel
     fields:
       name:
         type: string
       arches:
         type: array
         array_item_type:
           type: string

Multiple Validations
~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   ---
   type: template
   name: validated-template
   content: |
     name: {{ ValidatedModel.name }}
     code: {{ ValidatedModel.code }}
     score: {{ ValidatedModel.score }}
   model:
     name: ValidatedModel
     fields:
       name:
         type: string
         validation:
           min-length: 1
           max-length: 50
       code:
         type: string
         validation:
           regex: "^[A-Z]{3}-[0-9]{3}$"
       score:
         type: int
         validation:
           min-value: 0
           max-value: 100


YAML Fields
-----------

Required Fields
~~~~~~~~~~~~~~~

``type`` (str)
   The type of the object, must be ``template``

``name`` (str)
   The name of the template. Objects with matching ``type`` will trigger this template's expansion.


Optional Fields
~~~~~~~~~~~~~~~

``content`` (str)
   Inline Jinja2 template content. Cannot be used together with ``file``.

``file`` (str)
   Path to external Jinja2 template file (relative to the YAML file location).
   Cannot be used together with ``content``.

``defaults`` (dict)
   Default values that merge with call data before validation.

``model`` (dict)
   Model definition for data validation. Structure:

   - **``name``** (str): Name of the model class (used for template access)
   - **``description``** (str, optional): Model description
   - **``fields``** (dict): Field definitions mapping field names to field specs

   Each field spec supports:

   - **``type``** (str): Field type (required)
   - **``alias``** (str, optional): Input field name alias
   - **``description``** (str, optional): Field documentation
   - **``default``** (any, optional): Default value
   - **``required``** (bool, optional): Whether field is required (default: ``true``)
   - **``validation``** (dict, optional): Validation rules
   - **``array_item_type``** (dict, optional): For ``array`` types, defines item type
   - **``object_fields``** (dict, optional): For ``object`` types, defines nested fields
   - **``object_type_name``** (str, optional): For ``object`` types, name for nested type

   Validation rule keys:

   - **``min-length``** (int): Minimum string length
   - **``max-length``** (int): Maximum string length
   - **``min-value``** (float): Minimum numeric value
   - **``max-value``** (float): Maximum numeric value
   - **``regex``** (str): Regular expression pattern
   - **``enum``** (list): List of allowed values (for enum type)

``description`` (str)
   Optional description of the template.


Error Handling
--------------

Template validation errors provide detailed information:

.. code-block:: text

   ValidationError: 1 validation error for TagModel
   name
     Field name must be at least 3 long (type=value_error)
     at data/templates.yaml:15:5

Errors include:
- Field name and path
- Validation rule that failed
- File and line number location
- Suggested corrections


Best Practices
--------------

1. **Use Models for Validation**: Define models for templates that need input validation
2. **Descriptive Field Names**: Use clear field names that match template usage
3. **Type Safety**: Define typed arrays and nested objects for better validation
4. **Validation Rules**: Add appropriate validation rules to catch errors early
5. **Defaults**: Use template defaults to reduce repetition in call data
6. **Documentation**: Add descriptions to models and fields for clarity
7. **External Files**: Use external template files for complex templates


Technical Reference
-------------------

For developers: The template system is implemented by the
:class:`koji_habitude.templates.Template` class. Model definitions create Pydantic
models via :class:`koji_habitude.templates.TemplateModelDefinition`. Templates use
Jinja2 for rendering and support full Jinja2 syntax and filters.

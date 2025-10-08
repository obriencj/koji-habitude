Exception Handling
==================

koji-habitude provides a comprehensive exception hierarchy that correlates errors with their source in YAML files, templates, and koji objects. All exceptions include rich context information to help diagnose and fix issues quickly.

Exception Hierarchy
-------------------

All koji-habitude exceptions inherit from ``HabitudeError``, which provides:

- **filename** - The YAML file where the error originated
- **lineno** - The line number in the YAML file
- **trace** - Template expansion chain (when applicable)
- **original_exception** - The underlying exception (pydantic, jinja2, koji, etc.)

Exception Types
---------------

YAML Parsing Errors
~~~~~~~~~~~~~~~~~~~

``YAMLError``
    Wraps ``yaml.YAMLError`` when YAML files cannot be parsed.

    **Example:**

    .. code-block:: text

        YAML Error:
        YAML parsing error: while parsing a block mapping
          Location: /data/tags/broken.yaml:4

Validation Errors
~~~~~~~~~~~~~~~~~

``ValidationError``
    Wraps pydantic validation errors when object data fails schema validation.

    Shows which fields failed validation and why.

    **Example:**

    .. code-block:: text

        Validation Error:
        Validation error for tag 'fedora-42-build' (2 validation errors):
          - arches: field required
          - extra_arches: Extra inputs are not permitted
          Location: /data/tags/fedora.yaml:42
          Template trace:
            - build-tag-template in /templates/common.yaml:15

Template Errors
~~~~~~~~~~~~~~~

``TemplateError``
    Base class for all template-related errors. Wraps Jinja2 errors with template context.

``TemplateSyntaxError``
    Wraps Jinja2 syntax errors when template content has invalid syntax.

    **Example:**

    .. code-block:: text

        Template Error:
        Error in template 'build-tag-template': unexpected '}'
          Location: /templates/common.yaml:15
          Template file: common-content.j2
          Template line: 23

``TemplateRenderError``
    Wraps Jinja2 rendering errors such as undefined variables.

    **Example:**

    .. code-block:: text

        Template Error:
        Error in template 'build-tag-template': 'arch' is undefined
          Location: /templates/common.yaml:15
          Template trace:
            - build-tag-template in /templates/common.yaml:15

``TemplateOutputError``
    Raised when a template renders successfully but produces invalid output (invalid YAML or objects that fail validation).

    **Example:**

    .. code-block:: text

        Template Error:
        Invalid output from template 'build-tag-template': Template rendered invalid YAML
          Location: /templates/common.yaml:15

Namespace Errors
~~~~~~~~~~~~~~~~

``ExpansionError``
    Raised when template expansion fails, such as when a referenced template cannot be found.

    Shows which templates are available to help identify typos.

    **Example:**

    .. code-block:: text

        Template Error:
        Could not resolve template: missing-template
          Available templates: build-tag, release-tag, test-template
          Location: /data/calls.yaml:10

``RedefineError``
    Raised when attempting to redefine an object in the namespace (when ``redefine=Redefine.ERROR``).

    Shows both the original and new object locations.

    **Example:**

    .. code-block:: text

        Redefinition Error:
        Redefinition of tag 'fedora-42-build'
          Original: /data/tags.yaml:42
          New: /data/duplicate.yaml:5
          Location: /data/duplicate.yaml:5

Koji API Errors
~~~~~~~~~~~~~~~

``KojiError``
    Base class for koji API errors. All koji errors include object context.

``ChangeReadError``
    Wraps ``koji.GenericError`` exceptions during the query/read phase when fetching current koji state.

    **Example:**

    .. code-block:: text

        Koji Error:
        Koji error during query for tag 'fedora-42-build'
          Error: ServerOffline: database outage in progress
          Location: /data/tags/fedora.yaml:42

``ChangeApplyError``
    Wraps ``koji.GenericError`` exceptions during the apply phase when writing changes to koji.

    Includes the specific change that failed and the koji method that was called.

    **Example:**

    .. code-block:: text

        Koji Error:
        Koji error during apply changes for tag 'fedora-42-build'
          Koji method: createTag
          Parameters: {'args': ('fedora-42-build',), 'kwargs': {'arches': 'x86_64'}}
          Error: TagAlreadyExists: tag fedora-42-build already exists
          Change: Create tag 'fedora-42-build'
          Location: /data/tags/fedora.yaml:42
          Template trace:
            - build-tag-template in /templates/common.yaml:15

Template Trace
--------------

When errors occur in objects created from templates, the **template trace** shows the full expansion chain:

.. code-block:: text

    Template trace:
      - build-tag-template in /templates/common.yaml:15
      - release-tags in /templates/release.yaml:42
      - platform-release in /templates/platforms.yaml:10

This shows that:

1. ``platform-release`` template (line 10 of platforms.yaml) was called
2. Which expanded to ``release-tags`` template (line 42 of release.yaml)
3. Which expanded to ``build-tag-template`` (line 15 of common.yaml)
4. Which finally produced the object that caused the error

The trace makes it easy to track down where configuration problems originate, even through multiple levels of template expansion.

Exception Chaining
------------------

All wrapped exceptions preserve the original exception via Python's exception chaining (``raise ... from e``):

- Access the original exception via ``exception.__cause__``
- Stack traces show both the wrapper and original exception
- You can catch either the wrapper (e.g., ``TemplateError``) or the original (e.g., ``jinja2.TemplateSyntaxError``)

Example:

.. code-block:: python

    from koji_habitude.exceptions import TemplateSyntaxError
    from jinja2.exceptions import TemplateSyntaxError as Jinja2Error

    try:
        # ... code that might fail ...
    except TemplateSyntaxError as e:
        # Catches our wrapped exception with rich context
        print(e)  # Shows full context
        print(e.__cause__)  # Shows original jinja2 error
    except Jinja2Error as e:
        # This will also catch it (exception chaining)
        print("Caught original jinja2 error")

CLI Error Display
-----------------

The CLI ``catchall`` decorator in ``koji_habitude.cli.util`` provides user-friendly error display:

- Each exception type is clearly labeled
- Full context is displayed (file location, template trace)
- Original error details are included for debugging
- Users see exactly what to fix and where

State Machine Errors
--------------------

The following exceptions are **not** part of the ``HabitudeError`` hierarchy, as they represent programming errors rather than user data errors:

- ``ProcessorStateError`` - Invalid processor state transitions
- ``ChangeError`` - Invalid change state transitions
- ``ChangeReportError`` - Invalid change report state transitions
- ``WorkflowStateError`` - Invalid workflow state transitions

These should not occur during normal operation and indicate bugs in the code.

Best Practices
--------------

When catching exceptions:

1. **Catch specific types** when you know what to expect:

   .. code-block:: python

       try:
           namespace.expand()
       except ExpansionError as e:
           logger.error(f"Template expansion failed: {e}")

2. **Catch HabitudeError** to handle all user data errors:

   .. code-block:: python

       try:
           workflow.run()
       except HabitudeError as e:
           # All user-facing errors
           print(f"Error: {e}")
           return 1

3. **Access original exceptions** for detailed debugging:

   .. code-block:: python

       try:
           namespace.to_object(data)
       except ValidationError as e:
           # Show our formatted error
           print(e)
           # Access pydantic's detailed error
           if e.original_exception:
               for error in e.original_exception.errors():
                   print(f"  Field: {error['loc']}")
                   print(f"  Type: {error['type']}")

4. **Use exception attributes** to programmatically handle errors:

   .. code-block:: python

       try:
           processor.run()
       except ChangeApplyError as e:
           logger.error(f"Failed to apply changes to {e.typename} '{e.name}'")
           logger.error(f"  File: {e.filename}:{e.lineno}")
           logger.error(f"  Change: {e.change_description}")
           logger.error(f"  Koji method: {e.method_name}")

API Reference
-------------

.. automodule:: koji_habitude.exceptions
    :members:
    :undoc-members:
    :show-inheritance:

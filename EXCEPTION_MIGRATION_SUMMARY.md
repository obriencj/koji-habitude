# Exception Migration Summary

## Completed Changes

### 1. New Exception Hierarchy (koji_habitude/exceptions.py)
Created a comprehensive exception hierarchy with the following classes:

- **`HabitudeError`** - Base exception with rich context (filename, lineno, trace, original_exception)
- **`YAMLError`** - Wraps yaml.YAMLError with file context
- **`ValidationError`** - Wraps pydantic.ValidationError with object and file context
- **`TemplateError`** - Base for template errors, wraps Jinja2 errors
  - **`TemplateSyntaxError`** - Wraps jinja2 syntax errors
  - **`TemplateRenderError`** - Wraps jinja2 rendering errors (undefined variables, etc.)
  - **`TemplateOutputError`** - When template renders invalid YAML or produces invalid objects
- **`ExpansionError`** - Enhanced with context about template calls and available templates
- **`RedefineError`** - Enhanced with structured context about both objects
- **`KojiError`** - Base for koji API errors
  - **`KojiQueryError`** - Errors during query/read phase
  - **`KojiApplyError`** - Errors during apply/write phase

All exceptions now include:
- Filename and line number where the error originated
- Template trace (showing template expansion chain)
- Original exception (for debugging and selective catching)
- Formatted error messages with all context

### 2. Updated koji_habitude/templates.py
- Imports new exception classes
- Wraps all Jinja2 errors in appropriate exception types
- Wraps YAML parsing errors in template output
- Removed old `TemplateException` and `TemplateValueError` classes entirely

### 3. Updated koji_habitude/namespace.py
- Imports and uses new `ValidationError`, `ExpansionError`, `RedefineError`
- Wraps pydantic validation errors in `to_object()` with full context
- Enhanced `ExpansionError` with template name, call context, and available templates list
- Enhanced `RedefineError` with structured object information
- Removed old exception definitions (now in exceptions.py)

### 4. Updated koji_habitude/loader.py
- Wraps yaml.YAMLError in `YAMLError` with filename context

### 5. Updated koji_habitude/__init__.py
- Re-exports all exception classes for convenient importing

### 6. Updated koji_habitude/cli/util.py
- Enhanced `catchall` decorator to handle new exception hierarchy
- Displays rich error context from `HabitudeError` exceptions
- Specific handlers for YAML, Validation, Template, Expansion, Redefine, and Koji errors
- Each exception type shows its formatted message with file location and template trace

### 7. Updated koji_habitude/models/change.py
- Enhanced `ChangeReport.compare()` to wrap koji query errors
  - When VirtualCall results are accessed (e.g., `self._taginfo.result`), `koji.GenericError` is wrapped in `ChangeReadError`
  - Takes the object directly rather than individual attributes for cleaner code
  - Includes object context (type, name, file location, template trace) in the error
- Enhanced `ChangeReport.check_results()` to wrap koji apply errors
  - When change results are checked (e.g., `change.result()`), `koji.GenericError` is wrapped in `ChangeApplyError`
  - Takes the object directly rather than individual attributes for cleaner code
  - Extracts koji method name and parameters from the VirtualCall object
  - Includes object context, change description, and koji method details

## Test Updates Required

The following tests need to be updated to work with the new exception system. Since the old exception classes were completely removed (not deprecated), these tests will fail until updated.

### tests/test_templates.py

#### 1. test_jinja2_error_propagation (line 517)
**Current:** Expects `jinja2.exceptions.TemplateSyntaxError`
**Needs:** Change to expect `koji_habitude.exceptions.TemplateSyntaxError`
```python
# Change from:
from jinja2.exceptions import TemplateSyntaxError
with self.assertRaises(TemplateSyntaxError):

# To:
from koji_habitude.exceptions import TemplateSyntaxError
with self.assertRaises(TemplateSyntaxError):
```

#### 2. test_render_with_validation_failure (line 322)
**Current:** Expects `TemplateValueError`
**Needs:** Change to expect `TemplateRenderError`
```python
# Change from:
with self.assertRaises(TemplateValueError) as context:

# To:
from koji_habitude.exceptions import TemplateRenderError
with self.assertRaises(TemplateRenderError) as context:
```

#### 3. test_template_content_validation (line 149)
**Current:** Expects `TemplateException`
**Needs:** Change to expect `TemplateError` from new module
```python
# Change from:
from koji_habitude.templates import TemplateException
with self.assertRaises(TemplateException) as context:

# To:
from koji_habitude.exceptions import TemplateError
with self.assertRaises(TemplateError) as context:
```

#### 4. test_template_file_path_validation (line 172)
**Current:** Expects `jinja2.exceptions.TemplateNotFound`
**Needs:** Change to expect `TemplateError` (which wraps TemplateNotFound)
```python
# Change from:
from jinja2.exceptions import TemplateNotFound
with self.assertRaises(TemplateNotFound) as context:

# To:
from koji_habitude.exceptions import TemplateError
with self.assertRaises(TemplateError) as context:
```

#### 5. test_template_value_error_inheritance (line 887)
**Current:** Tests old `TemplateValueError` class
**Needs:** Remove this test entirely - the class no longer exists

#### 6. test_template_value_error_usage (line 899)
**Current:** Tests old `TemplateValueError` class
**Needs:** Remove this test entirely - the class no longer exists

### tests/test_expansion.py

#### 1. test_invalid_jinja2_syntax_error (line 291)
**Current:** Expects `jinja2.exceptions.TemplateSyntaxError`
**Needs:** Change to expect `koji_habitude.exceptions.TemplateSyntaxError`
```python
# Change from:
from jinja2.exceptions import TemplateSyntaxError
with self.assertRaises(TemplateSyntaxError):

# To:
from koji_habitude.exceptions import TemplateSyntaxError
with self.assertRaises(TemplateSyntaxError):
```

#### 2. test_meta_template_generates_invalid_template (line 300)
**Current:** Expects `pydantic.ValidationError`
**Needs:** Change to expect `koji_habitude.exceptions.ValidationError`
```python
# Change from:
from pydantic import ValidationError
with self.assertRaises(ValidationError):

# To:
from koji_habitude.exceptions import ValidationError
with self.assertRaises(ValidationError):
```

## Example Error Messages

### Before (pydantic validation error):
```
ValidationError: 1 validation error for Tag
name
  Field required [type=missing, input_value=..., input_type=dict]
```

### After (wrapped validation error):
```
Validation error for tag 'fedora-42-build' (1 validation error):
  - name: Field required
  Location: /data/tags/fedora.yaml:42
  Template trace:
    - build-tag-template in /templates/common.yaml:15
  Original error: ValidationError: 1 validation error for Tag
name
  Field required [type=missing, input_value=..., input_type=dict]
```

### Before (jinja2 template syntax error):
```
jinja2.exceptions.TemplateSyntaxError: unexpected '}'
```

### After (wrapped template syntax error):
```
Error in template 'build-tag-template': unexpected '}'
  Location: /templates/common.yaml:15
  Template file: common-content.j2
  Template line: 23
  Original error: TemplateSyntaxError: unexpected '}'
```

### Before (expansion error):
```
ExpansionError: Could not resolve template: missing-template
```

### After (enhanced expansion error):
```
Could not resolve template: missing-template
  Available templates: build-tag, release-tag, test-template
  Location: /data/calls.yaml:10
  Template trace:
    - parent-template in /templates/parent.yaml:5
```

## Migration Notes

### Removed Classes
The following classes have been completely removed from `koji_habitude/templates.py`:
- `TemplateException` - replaced by `TemplateError` in `koji_habitude.exceptions`
- `TemplateValueError` - replaced by `TemplateRenderError` or `TemplateOutputError` in `koji_habitude.exceptions`

### Import Changes
All new exception classes are re-exported from `koji_habitude/__init__.py`:
```python
from koji_habitude import ValidationError, TemplateError, ExpansionError
```

### Exception Chaining
All wrapped exceptions use `raise ... from e` to maintain exception chains:
- `exception.__cause__` contains the original exception
- Stack traces show both the wrapper and original exception
- Can catch either the wrapper or original exception type

### No Backward Compatibility
Since this project is not yet released, the old exception classes were completely removed:
- No deprecation warnings
- No wrapper classes for compatibility
- Clean migration to new exception hierarchy

## Benefits

1. **Better Error Messages** - Users see exactly where the problem is (file:line) and how they got there (template trace)

2. **Easier Debugging** - Template expansion chains are visible, making it clear which template generated what

3. **Consistent Interface** - All exceptions have the same attributes (filename, lineno, trace, original_exception)

4. **Selective Catching** - Can catch broad categories (`HabitudeError`) or specific types (`TemplateSyntaxError`)

5. **Preserved Stack Traces** - Original exceptions are accessible via `__cause__` for deep debugging

## Exception Usage Summary

### Actively Raised ✅
1. **`YAMLError`** - Raised in `loader.py` when YAML parsing fails
2. **`ValidationError`** - Raised in `namespace.py` when pydantic validation fails
3. **`TemplateError`** - Raised in `templates.py` for general template errors
4. **`TemplateSyntaxError`** - Raised in `templates.py` for Jinja2 syntax errors
5. **`TemplateRenderError`** - Raised in `templates.py` for rendering errors (undefined variables, etc.)
6. **`TemplateOutputError`** - Raised in `templates.py` for invalid template output
7. **`ExpansionError`** - Raised in `namespace.py` for template expansion failures
8. **`RedefineError`** - Raised in `namespace.py` for object redefinitions
9. **`ChangeReadError`** - Raised in `models/change.py` when koji query results fail (during compare phase)
10. **`ChangeApplyError`** - Raised in `models/change.py` when koji apply operations fail (during check_results phase)
11. **`KojiError`** - Generic base class, caught as fallback in CLI

### Not Changed

The following exception classes were intentionally NOT migrated (they are internal state machine errors):
- `ProcessorStateError` (processor.py)
- `ChangeError` (models/change.py)
- `ChangeReportError` (models/change.py)
- `WorkflowStateError` (workflow.py)
- `WorkflowPhantomsError` (workflow.py) - though this could be enhanced in the future

These represent programming errors (calling methods in wrong order) rather than user data errors, so they remain simple exception classes.

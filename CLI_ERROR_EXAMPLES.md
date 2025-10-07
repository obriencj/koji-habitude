# CLI Error Display Examples

This document shows how different errors are displayed in the CLI after the exception migration.

## YAML Error

**Before:**
```
[ValidationError] 1 validation error for ...
```

**After:**
```
YAML Error:
YAML parsing error: while parsing a block mapping
  in "<unicode string>", line 3, column 1
expected <block end>, but found '<block mapping start>'
  in "<unicode string>", line 4, column 3
  Location: /data/tags/broken.yaml:4
```

## Validation Error

**Before:**
```
[ValidationError] 1 validation error for Tag
name
  Field required [type=missing, input_value=..., input_type=dict]
```

**After:**
```
Validation Error:
Validation error for tag 'fedora-42-build' (1 validation error):
  - name: Field required
  Location: /data/tags/fedora.yaml:42
  Template trace:
    - build-tag-template in /templates/common.yaml:15
  Original error: ValidationError: 1 validation error for Tag
name
  Field required [type=missing, input_value=..., input_type=dict]
```

## Template Syntax Error

**Before:**
```
[Error] unexpected '}'
```

**After:**
```
Template Error:
Error in template 'build-tag-template': unexpected '}'
  Location: /templates/common.yaml:15
  Template file: common-content.j2
  Template line: 23
  Original error: TemplateSyntaxError: unexpected '}'
```

## Template Rendering Error (Undefined Variable)

**Before:**
```
[Error] 'arch' is undefined
```

**After:**
```
Template Error:
Error in template 'build-tag-template': 'arch' is undefined
  Location: /templates/common.yaml:15
  Template trace:
    - build-tag-template in /templates/common.yaml:15
  Original error: UndefinedError: 'arch' is undefined
```

## Template Output Error

**Before:**
```
[Error] expected <block end>, but found '<block mapping start>'
```

**After:**
```
Template Error:
Invalid output from template 'build-tag-template': Template rendered invalid YAML: expected <block end>, but found '<block mapping start>'
  Location: /templates/common.yaml:15
  Template trace:
    - build-tag-template in /templates/common.yaml:15
  Original error: YAMLError: expected <block end>, but found '<block mapping start>'
```

## Expansion Error

**Before:**
```
[Error] Could not resolve template: missing-template
```

**After:**
```
Template Error:
Could not resolve template: missing-template
  Available templates: build-tag, release-tag, test-template
  Location: /data/calls.yaml:10
  Template trace:
    - parent-template in /templates/parent.yaml:5
```

## Redefinition Error

**Before:**
```
[Error] Redefinition of ('tag', 'fedora-42-build') at /data/duplicate.yaml:5 (original /data/tags.yaml:42)
```

**After:**
```
Redefinition Error:
Redefinition of tag 'fedora-42-build'
  Original: /data/tags.yaml:42
  New: /data/duplicate.yaml:5
  Location: /data/duplicate.yaml:5
```

## Change Read Error

**Before:**
```
[Error] ServerOffline: database outage in progress
```

**After:**
```
Koji Error:
Koji error during query for tag 'fedora-42-build'
  Error: ServerOffline: database outage in progress
  Location: /data/tags/fedora.yaml:42
  Template trace:
    - build-tag-template in /templates/common.yaml:15
  Original error: ServerOffline: database outage in progress
```

**Note:** This is raised as `ChangeReadError` to reflect that it's a change report read/query error.

## Change Apply Error

**Before:**
```
[GenericError] Tag already exists: fedora-42-build
```

**After:**
```
Koji Error:
Koji error during apply changes for tag 'fedora-42-build'
  Koji method: createTag
  Parameters: {'args': ('fedora-42-build',), 'kwargs': {'arches': 'x86_64'}}
  Error: TagAlreadyExists: tag fedora-42-build already exists
  Change: Create tag 'fedora-42-build'
  Location: /data/tags/fedora.yaml:42
  Template trace:
    - build-tag-template in /templates/common.yaml:15
  Original error: TagAlreadyExists: tag fedora-42-build already exists
```

**Note:** This is raised as `ChangeApplyError` to reflect that it's a change application error. The method name and parameters are extracted from the VirtualCall object to provide detailed debugging information.

**After (when not wrapped - direct from koji):**
```
Koji Error: Tag already exists: fedora-42-build
```

## Authentication Error

**Before:**
```
[GSSAPIAuthError] Could not initialize GSSAPI: ...
```

**After:**
```
Authentication Error: Could not initialize GSSAPI: ...
```

## Benefits of New Error Display

1. **Clear Context** - Users immediately see which file and line caused the problem
2. **Template Tracing** - Shows the full chain of template expansions that led to the error
3. **Actionable Information** - Users know exactly where to look and what to fix
4. **Original Errors Preserved** - Advanced users can see the underlying exception details
5. **Categorized Errors** - Different error types are clearly labeled (YAML Error, Template Error, etc.)

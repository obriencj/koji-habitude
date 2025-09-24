# Unit Testing Rules for koji-habitude

## Overview
This document defines the testing standards and conventions for the koji-habitude project. These rules ensure consistency, maintainability, and reliability across all test code.

## Test File Organization

### Test File Naming and Structure
- Test files must focus on a single module of the `koji_habitude` package at a time
- Test files should be named `test_{module_name}.py` where `{module_name}` matches the module being tested
- Examples:
  - `test_loader.py` tests `koji_habitude.loader`
  - `test_templates.py` tests `koji_habitude.templates`
  - `test_cli.py` tests `koji_habitude.cli`

### Test Data Organization
All test data must be stored under the `tests/data` directory with the following structure:

#### `tests/data/bad/`
- Contains intentionally malformed or invalid data for negative testing
- Files should have descriptive names indicating the type of problem
- Examples:
  - `malformed_yaml.yaml` - YAML syntax errors
  - `missing_required_fields.yaml` - Missing mandatory schema fields
  - `invalid_schema.yaml` - Schema validation failures
  - `circular_dependencies.yaml` - Dependency resolution issues

#### `tests/data/templates/`
- Contains pure template definitions for template-focused tests
- Should include various template scenarios:
  - Simple templates
  - Templates with Jinja2 expansions
  - Templates with dependencies
  - Multi-object templates

#### `tests/data/samples/`
- Contains complete sample data that may employ templates
- May embed both model units and templates in single files
- Should represent realistic usage scenarios
- Examples of complete workflows and object definitions

### File Usage Restrictions
- **NO tempfiles**: All test data must come from the `tests/data` directory
- **NO file copying**: Tests should use existing files from the data directory directly
- **NO file modification**: Tests should not modify existing data files during execution
- **NO dynamic file creation**: All test data should be pre-created and version controlled

## Test Code Standards

### Module Docstrings
Every test file must start with a module docstring following this format:
```python
"""
koji-habitude - test_{module_name}

Unit tests for koji_habitude.{module_name} module.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""
```

### Function and Class Naming
- Test functions should use descriptive names starting with `test_`
- Use snake_case for test function names
- Names should clearly indicate what is being tested
- Examples:
  - `test_load_template_from_valid_yaml()`
  - `test_resolve_dependencies_with_circular_reference()`
  - `test_cli_command_with_missing_profile()`

### Test Structure and Organization
- Group related tests in test classes when appropriate
- Use `setUp()` and `tearDown()` methods for common test initialization/cleanup
- Each test should focus on a single aspect or behavior
- Tests should be independent and able to run in any order

### String Quote Conventions
Follow the project's string quote conventions:
- Use single quotes for identifiers and simple keys (type names, dictionary keys, etc.)
- Use double quotes for human-readable text (error messages, descriptions, assertions)

### File Ending
Every test file must end with a comment containing exactly `# The end.` and a single newline

## Test Data Standards

### YAML Data Files
- All YAML files must be valid and parseable unless specifically testing malformed data
- Use consistent indentation (2 spaces)
- Include meaningful comments explaining the purpose of complex test data
- Follow the project's object schema definitions

### Data File Documentation
- Each data directory should contain a `README.md` explaining its contents
- Complex test scenarios should be documented within the data files themselves
- Bad data files should include comments explaining why they are invalid

### File Count Maintenance
**IMPORTANT**: When adding or removing files from the `tests/data/` directory, you **MUST** update the global file count constants at the top of `tests/test_loader.py`:

- `TEMPLATES_YAML_COUNT` - Count of `.yaml` and `.yml` files in `tests/data/templates/`
- `TEMPLATES_J2_COUNT` - Count of `.j2` files in `tests/data/templates/`
- `SAMPLES_YAML_COUNT` - Count of `.yaml/.yml` files in `tests/data/samples/` (including nested)
- `BAD_YAML_COUNT` - Count of `.yaml/.yml` files in `tests/data/bad/`
- `BAD_TOTAL_COUNT` - Count of all files in `tests/data/bad/`

Failure to update these constants will cause loader tests to fail with incorrect file count assertions.

## Testing Patterns

### Path Handling
- Use absolute paths when referencing test data files
- Construct paths using `pathlib.Path`
- Example: `test_data_path = Path(__file__).parent / 'data' / 'templates' / 'simple.yaml'`

### Error Testing
- Test both positive and negative cases
- Use appropriate assertion methods for expected exceptions
- Verify specific error messages and types when testing error conditions
- Example:
```python
with self.assertRaises(ValidationError) as context:
    load_malformed_data()
self.assertIn("missing required field", str(context.exception))
```

### Mock Usage
- Use mocks sparingly and only when necessary (e.g., koji client interactions)
- Prefer real data over mocked data when possible
- When mocking koji client calls, use realistic response data
- Document why mocking is necessary in test comments

### Assertion Guidelines
- Use the most specific assertion method available
- Include meaningful failure messages in assertions
- Test both the expected result and its type when appropriate
- Examples:
  - `self.assertEqual(result, expected, "Template expansion failed")`
  - `self.assertIsInstance(loaded_object, TargetModel)`
  - `self.assertIn('tag-name', resolved_dependencies)`

## Anti-Patterns and Forbidden Practices

### Never Write Tests That Pass Due to Bugs
**CRITICAL**: Unit tests must NEVER be written to pass by depending on bugs or exceptions from broken code.

#### Forbidden Patterns
- **DO NOT** write tests that expect exceptions from what you think are bugs
- **DO NOT** use `with self.assertRaises(Exception):` to make tests pass when you suspect implementation problems
- **DO NOT** write comments like "This test documents the current behavior until the implementation is fixed"
- **DO NOT** hide bugs by making tests pass through exception expectations

#### Correct Approach
- **DO** write tests that validate the intended behavior of your code
- **DO** write tests that will fail if there are actual bugs
- **DO** fix bugs in the implementation, not in the tests
- **DO** write tests that document the correct expected behavior

#### Example of Bad Test (DO NOT DO THIS)
```python
def test_some_functionality(self):
    # The current implementation has a bug - it doesn't include 'type' field
    # This test documents the current behavior until the implementation is fixed
    with self.assertRaises(Exception):
        result = some_function()
```

#### Example of Good Test (DO THIS)
```python
def test_some_functionality(self):
    result = some_function()
    self.assertIsInstance(result, ExpectedType)
    self.assertEqual(result.field1, expected_value)
    self.assertEqual(result.field2, expected_value)
```

### Test Philosophy
- **Tests should fail when code is broken**
- **Tests should pass when code works correctly**
- **Tests should document intended behavior, not current bugs**
- **If you find a bug, fix the implementation, not the test**

### When You Suspect a Bug
1. **Investigate the implementation** to understand what it should do
2. **Write a test that validates the correct behavior**
3. **Fix the implementation** to make the test pass
4. **Never write a test that passes by expecting the bug to raise an exception**

## Test Coverage Requirements

### Functional Coverage
- Test all public functions and methods
- Include edge cases and boundary conditions
- Test error handling and exception paths
- Verify integration between related components

### Data Coverage
- Test with various valid data formats
- Test with all supported koji object types (tag, external-repo, user, target, host, group)
- Test template expansion scenarios
- Test dependency resolution patterns

### CLI Coverage
- Test all CLI commands and subcommands
- Test with various argument combinations
- Test error conditions (missing files, invalid profiles, etc.)
- Test help output and usage messages

## Maintenance Guidelines

### Adding New Tests
- Follow the established naming and organization patterns
- Add corresponding test data files as needed
- Update this document if new testing patterns emerge
- Ensure new tests pass the project's linting and formatting standards

### Updating Test Data
- Version control all test data changes
- Document the purpose of test data modifications
- Ensure changes don't break existing tests
- Consider backward compatibility when modifying shared test data

### Future Extensions
This document may be extended with additional rules as the project evolves. Common areas for future expansion:
- Performance testing guidelines
- Integration testing standards
- Continuous integration requirements
- Test reporting and metrics standards

## Tools and Dependencies

### Testing Framework
- Use Python's built-in `unittest` framework
- Import specific assertion methods as needed
- Utilize `unittest.mock` for necessary mocking scenarios

### Test Runner
- A simple test entrypoint is via `make quicktest`
- When you want to run pytest, invoke it via `tox -qe quicktest -- `
- More detailed test data is runnable via `tox -qe quicktest -- -v`
- Individual test files should be runnable directly via `tox -qe quicktest -- [testfile] -v`
- Follow the project's existing test execution patterns

### Linting and Formatting
- All test code must pass the same linting standards as production code
- Follow PEP 8 style guidelines
- Use the project's configured linting tools (flake8, etc.)

---

*This document serves as the authoritative guide for unit testing in the koji-habitude project. All contributors should familiarize themselves with these rules before writing tests.*

# TODO - Future Features

This document tracks planned features and improvements for koji-habitude.

## ✅ Recently Completed

**CLI Framework and Core Commands**:
- [x] Fix CLI import errors and convert from Clique to Click
- [x] Implement basic CLI structure with subcommands
- [x] Add `sync` command framework (ready for implementation)
- [x] Add `diff` command (calls sync with --dry-run)
- [x] Add `list-templates` command with basic functionality
- [x] Add `validate` command framework (ready for implementation)
- [x] Add `expand` command for template expansion and YAML output
- [x] Update documentation to reflect current state
- [x] Fix namespace import issues (RawObject → BaseObject)

**Data Model and Schemas**:
- [x] Implement comprehensive CORE_MODELS schemas (Channel, ExternalRepo, Group,
  Host, Permission, Tag, Target, User)
- [x] Add Pydantic validation with proper field constraints and aliases
- [x] Implement dependency resolution methods for all model types
- [x] Add splitting functionality for models that support tiered execution
- [x] Create robust base classes (BaseObject, BaseKojiObject) with common
  functionality

**Unit Testing Infrastructure**:
- [x] Add comprehensive unit tests for all CORE_MODELS (50 test cases)
- [x] Test model creation, validation, dependency resolution, and splitting
- [x] Test registry consistency and model behavior verification
- [x] Test Pydantic validation and field constraints
- [x] Document implementation bugs found during testing

**Dependency Resolution Architecture**:
- [x] Implement Resolver module for external dependency resolution
- [x] Implement Solver module for tiered dependency resolution
- [x] Add Node-based dependency graph construction
- [x] Implement automatic splitting for cross-tier dependencies
- [x] Add priority-based execution ordering
- [x] Create MissingObject placeholder system for unresolved dependencies

## 🚀 Immediate Next Steps

**Core Implementation** (Ready for development):
- [ ] Implement `sync` command body with koji client integration
- [ ] Implement `validate` command body for offline validation
- [ ] Add error handling and user feedback throughout CLI
- [ ] Implement koji object diffing logic
- [ ] Add multicall support for efficient koji operations
- [ ] Test CLI commands with real data files

**Processor Module** (New architecture component):
- [ ] Implement model methods for koji integration (`fetch_koji_state`, `diff_against_koji`, `apply_to_koji`)
- [ ] Complete Processor class implementation with multicall integration
- [ ] Implement DiffOnlyProcessor for dry-run operations
- [ ] Add error handling and recovery for partial failures
- [ ] Implement change tracking and reporting
- [ ] Add progress reporting and status updates
- [ ] Test Processor with mock koji sessions
- [ ] Add unit tests for Processor and DiffOnlyProcessor classes

**Workflow Orchestration** (High-level coordination):
- [ ] Implement Workflow class for end-to-end process coordination
- [ ] Add missing object validation before processing
- [ ] Implement progress reporting and TUI integration
- [ ] Add error handling and rollback capabilities
- [ ] Create workflow configuration and options
- [ ] Add workflow testing with integration scenarios
- [ ] Document workflow usage and best practices

**Infrastructure**:
- [ ] Set up continuous integration testing
- [ ] Add type hints throughout codebase
- [ ] Implement proper logging configuration

## 🧪 Unit Testing

**Goal**: Comprehensive test coverage for core functionality.

**Current Status**: Extensive test coverage exists for core modules with 42 test
data files and comprehensive test suites (274 total tests).

**Test Data Structure**:
- `tests/data/templates/` - Template definition test files
- `tests/data/namespace/` - Namespace and expansion test scenarios
- `tests/data/samples/` - Valid sample data files
- `tests/data/bad/` - Invalid data for error handling tests
- `tests/data/demo/` - Demo scenarios and examples
- `tests/data/solver/` - Solver-specific test scenarios

**Test File Coverage**:
- `test_loader.py`: 52 tests (file loading, YAML parsing, error handling)
- `test_models.py`: 52 tests (CORE_MODELS validation, dependency resolution)
- `test_templates.py`: 32 tests (template expansion, Jinja2 processing)
- `test_expansion.py`: 14 tests (template expansion workflows)
- `test_namespace.py`: 53 tests (namespace handling, object resolution)
- `test_resolver.py`: 27 tests (dependency resolution algorithms)
- `test_solver.py`: 58 tests (tiered execution, splitting logic)

### ✅ Completed Test Coverage

**Data Schema Testing**:
- [x] Test YAML loading and validation (test_loader.py)
- [x] Test template schema validation (test_templates.py)
- [x] Test object data structure validation (test_namespace.py)
- [x] Test invalid data handling (test_loader.py with bad/ directory)

**Model Testing**:
- [x] Test CORE_MODELS creation and validation (test_models.py)
- [x] Test base model classes (BaseObject, BaseKojiObject, RawObject)
- [x] Test dependency resolution for all model types
- [x] Test splitting functionality where supported
- [x] Test Pydantic validation and field constraints
- [x] Test model registry consistency and behavior

**Template Testing**:
- [x] Test Jinja2 template expansion (test_templates.py)
- [x] Test recursive template processing (test_expansion.py)
- [x] Test template error handling (test_expansion.py)
- [x] Test template schema validation (test_templates.py)
- [x] Test external template file loading
- [x] Test template tracing and metadata
- [x] Test multi-document template processing

**Namespace and Expansion Testing**:
- [x] Test basic template expansion (test_expansion.py)
- [x] Test deferred resolution (test_expansion.py)
- [x] Test meta-template generation (test_expansion.py)
- [x] Test circular dependency detection (test_expansion.py)
- [x] Test complex dependency scenarios (test_expansion.py)

**Loader Testing**:
- [x] Test file finding and discovery (test_loader.py)
- [x] Test YAML document loading (test_loader.py)
- [x] Test MultiLoader functionality (test_loader.py)
- [x] Test error handling for malformed files (test_loader.py)

### 🚧 Missing Test Coverage

**CLI Testing**:
- [ ] Test CLI command parsing and options
- [ ] Test CLI error handling and user feedback
- [ ] Test CLI integration with core modules
- [ ] Test CLI help text and documentation

**Dependency Resolution Testing**:
- [x] Test Resolver module with various dependency scenarios (test_resolver.py - 27 tests)
- [x] Test Solver module tiered execution (test_solver.py - 58 tests)
- [x] Test Node-based dependency graph construction (test_solver.py)
- [x] Test automatic splitting for cross-tier dependencies (test_solver.py)
- [x] Test MissingObject placeholder system (test_resolver.py)
- [x] Test priority-based execution ordering (test_solver.py)

**Comparison Testing**:
- [ ] Test koji object diffing logic (once implemented)
- [ ] Test update call generation
- [ ] Test multicall result processing
- [ ] Mock koji responses for testing

**Processor Testing**:
- [ ] Test Processor class with mock koji sessions
- [ ] Test DiffOnlyProcessor dry-run functionality
- [ ] Test chunking behavior with various chunk sizes
- [ ] Test error handling for partial failures
- [ ] Test multicall integration and promise resolution
- [ ] Test change tracking and reporting accuracy
- [ ] Test progress reporting and status updates

**Integration Testing**:
- [ ] Test end-to-end workflows with real data
- [ ] Test CLI commands with various data combinations
- [ ] Test performance with large datasets
- [ ] Test error recovery and rollback scenarios

## ⚡ FakeHub Support

**Goal**: Ultra-fast operations using koji's FakeHub for direct database access.

- [ ] Research FakeHub API and requirements
- [ ] Add FakeHub client implementation
- [ ] Implement database connection handling
- [ ] Add authentication for database access
- [ ] Create FakeHub-specific resolver
- [ ] Add CLI option to enable FakeHub mode
- [ ] Document FakeHub setup requirements
- [ ] Performance benchmarking vs standard koji client

**Notes**:
- FakeHub only available from koji git repository
- Requires direct database access permissions
- Same core logic, different authentication/connection method

## 🎯 Type Filtering

**Goal**: Allow operations to be limited to specific object types.

**Status**: CLI framework ready, implementation pending.

- [ ] Add `--type` CLI option accepting comma-separated list
- [ ] Implement type filtering in object loading
- [ ] Update dependency resolution to respect type filters
- [ ] Handle cross-type dependencies gracefully
- [ ] Add validation for unknown type names
- [ ] Update help documentation

### Supported Type Names
- `external-repo` - External repositories
- `user` - Koji users
- `tag` - Build tags
- `target` - Build targets
- `host` - Build hosts
- `group` - Package groups
- `permission` - User permissions (future)

### Example Usage
```bash
# Only sync users and external repos
koji-habitude sync --type user,external-repo /path/to/data

# Only validate tag configurations
koji-habitude validate --type tag /path/to/data

# Diff only targets and their dependencies
koji-habitude diff --type target /path/to/data
```

## 📚 Documentation

**Goal**: Comprehensive documentation for users and developers.

**Current Status**: Basic Sphinx documentation structure exists with some content, but needs expansion and improvement.

### ✅ Completed Documentation Infrastructure

- [x] Configure project for building docs using Sphinx (setup.cfg with sphinx testenv)
- [x] Create documentation stubs (docs/ directory with basic structure)
- [x] Set up Sphinx configuration (docs/conf.py with autodoc, intersphinx)
- [x] Create overview documentation (docs/overview.rst from README.md)
- [x] Add Makefile targets for documentation building (docs, preview-docs, clean-docs)
- [x] Configure automatic overview regeneration from README.md
- [x] Set up basic API reference structure (docs/koji_habitude.rst)

### 🚧 Documentation Content Needs

**API Documentation**:
- [ ] Complete API reference for all modules (loader, models, namespace, resolver, solver, templates)
- [ ] Add comprehensive docstrings to all public functions and classes
- [ ] Document CLI command options and usage examples
- [ ] Add type hints documentation and examples
- [ ] Document error handling and exception types

**User Documentation**:
- [ ] Create comprehensive user guide with step-by-step tutorials
- [ ] Add YAML format specification and examples
- [ ] Document template system with advanced examples
- [ ] Create troubleshooting guide for common issues
- [ ] Add performance tuning and best practices guide

**Developer Documentation**:
- [ ] Document architecture and design decisions
- [ ] Create developer setup and contribution guide
- [ ] Document testing strategy and how to add tests
- [ ] Add code style and conventions documentation
- [ ] Document dependency resolution algorithms

**Examples and Tutorials**:
- [ ] Create complete example configurations
- [ ] Add tutorial for setting up a new koji instance
- [ ] Document common use cases and patterns
- [ ] Add migration guide from manual koji management
- [ ] Create troubleshooting scenarios with solutions

### 📋 Documentation Infrastructure Improvements

- [ ] Add sphinx-autodoc-typehints for better type documentation
- [ ] Configure sphinx extensions for better cross-referencing
- [ ] Add documentation versioning strategy
- [ ] Set up automated documentation deployment
- [ ] Add documentation testing to CI pipeline
- [ ] Create documentation style guide
- [ ] Add spell checking for documentation
- [ ] Configure documentation search functionality

### 📖 Documentation Quality

- [ ] Review and improve existing docstrings for clarity
- [ ] Ensure all public APIs have comprehensive documentation
- [ ] Add inline code examples to docstrings
- [ ] Standardize documentation format across all modules
- [ ] Add parameter and return value documentation
- [ ] Document side effects and important behaviors
- [ ] Add "See Also" sections for related functionality

## 🔮 Future Considerations

Items that may be added later:

- [ ] Integration with git hooks for automatic sync
- [ ] Backup/restore functionality
- [ ] Configuration drift detection
- [ ] Multi-hub synchronization
- [ ] Performance metrics and monitoring
- [ ] Rollback capabilities
- [ ] Configuration as Code (CaC) integrations

## 📝 Notes

**Current State**: The project has made significant progress on core
architecture:
- ✅ **CLI Framework**: Complete and functional with all commands available
- ✅ **Data Models**: All CORE_MODELS implemented with Pydantic validation
- ✅ **Unit Testing**: Comprehensive test coverage for models (50 test cases)
- ✅ **Dependency Resolution**: Resolver and Solver modules implemented for
  tiered execution
- 🚧 **Integration**: Ready for koji client integration and command body
  implementation

**Development Guidelines**:
- Maintain backward compatibility when adding new features
- All new features should include documentation updates
- Consider impact on existing CLI interface design
- Ensure new features align with functional programming principles
- Add appropriate error handling and user feedback
- Focus on implementing core `sync` and `validate` commands next

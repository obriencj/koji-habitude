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

## 🚀 Immediate Next Steps

**Core Implementation** (Ready for development):
- [ ] Implement `sync` command body with koji client integration
- [ ] Implement `validate` command body for offline validation
- [ ] Add error handling and user feedback throughout CLI
- [ ] Implement koji object diffing logic
- [ ] Add multicall support for efficient koji operations
- [ ] Test CLI commands with real data files

**Infrastructure**:
- [ ] Set up continuous integration testing
- [ ] Add type hints throughout codebase
- [ ] Implement proper logging configuration

## 🧪 Unit Testing

**Goal**: Comprehensive test coverage for core functionality.

**Current Status**: Extensive test coverage exists for core modules with 29 test data files and comprehensive test suites.

**Test Data Structure**:
- `tests/data/templates/` - Template definition test files
- `tests/data/namespace/` - Namespace and expansion test scenarios
- `tests/data/samples/` - Valid sample data files
- `tests/data/bad/` - Invalid data for error handling tests

### ✅ Completed Test Coverage

**Data Schema Testing**:
- [x] Test YAML loading and validation (test_loader.py)
- [x] Test template schema validation (test_templates.py)
- [x] Test object data structure validation (test_namespace.py)
- [x] Test invalid data handling (test_loader.py with bad/ directory)

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

**Comparison Testing**:
- [ ] Test koji object diffing logic (once implemented)
- [ ] Test update call generation
- [ ] Test multicall result processing
- [ ] Mock koji responses for testing

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

**Current State**: The CLI framework is functional and ready for core implementation. All commands are available with proper help text, but command bodies need implementation for full functionality.

**Development Guidelines**:
- Maintain backward compatibility when adding new features
- All new features should include documentation updates
- Consider impact on existing CLI interface design
- Ensure new features align with functional programming principles
- Add appropriate error handling and user feedback
- Focus on implementing core `sync` and `validate` commands next

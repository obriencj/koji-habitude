# TODO - Future Features

This document tracks planned features and improvements for koji-habitude.

## ✅ Recently Completed

**Core Implementation**:
- [x] Complete CLI framework with sync, diff, list-templates, and expand commands
- [x] All CORE_MODELS implemented with Pydantic validation and dependency resolution
- [x] Comprehensive unit testing (360 tests, 74% coverage)
- [x] Dependency resolution with Resolver and Solver modules for tiered execution
- [x] Processor module with multicall integration and change tracking
- [x] Workflow orchestration and koji profile support

## 🚀 Immediate Next Steps

**CLI Enhancements**:
- [ ] Add comprehensive error handling and user feedback
- [ ] Implement progress bars and better status reporting
- [ ] Enhance help text and documentation

**Workflow Improvements**:
- [ ] Implement progress reporting and TUI integration
- [ ] Create workflow configuration and options
- [ ] Add workflow testing with integration scenarios

**Infrastructure**:
- [ ] Set up continuous integration testing
- [ ] Add type hints throughout codebase
- [ ] Implement proper logging configuration
- [ ] Performance optimization and benchmarking

## 🧪 Testing Priorities

**Current Status**: 74% coverage (360 tests) - Core functionality well tested

**High Priority** (Major coverage impact):
- [ ] **CLI Module** (0% coverage, 106 statements) - Critical for user interaction
- [ ] **Loader Module** (70% coverage, 29 missing) - Core file loading functionality
- [ ] **Templates Module** (77% coverage, 33 missing) - Template processing edge cases

**Medium Priority**:
- [ ] **Processor Module** (87% coverage, 18 missing) - Chunking and error handling
- [ ] **Integration Testing** - End-to-end workflows with real data

## 🎯 Type Filtering

**Goal**: Allow operations to be limited to specific object types.

- [ ] Add `--type` CLI option accepting comma-separated list
- [ ] Implement type filtering in object loading and dependency resolution
- [ ] Handle cross-type dependencies gracefully
- [ ] Add validation for unknown type names

**Supported Types**: `external-repo`, `user`, `tag`, `target`, `host`, `group`, `permission`

## ⚡ FakeHub Support

**Goal**: Ultra-fast operations using koji's FakeHub for direct database access.

- [ ] Research FakeHub API and requirements
- [ ] Add FakeHub client implementation with database connection handling
- [ ] Add CLI option to enable FakeHub mode
- [ ] Performance benchmarking vs standard koji client

**Note**: Requires direct database access permissions and koji git repository.

## 📚 Documentation

**Current Status**: Basic Sphinx structure exists, needs content expansion.

**Priority Content**:
- [ ] Complete API reference for all modules
- [ ] Comprehensive user guide with tutorials
- [ ] YAML format specification and examples
- [ ] Template system documentation with advanced examples
- [ ] Troubleshooting guide for common issues

**Infrastructure**:
- [ ] Add sphinx-autodoc-typehints for better type documentation
- [ ] Set up automated documentation deployment
- [ ] Add documentation testing to CI pipeline

## 🔮 Future Considerations

**Potential Features**:
- [ ] Integration with git hooks for automatic sync
- [ ] Backup/restore functionality
- [ ] Configuration drift detection
- [ ] Multi-hub synchronization
- [ ] Performance metrics and monitoring
- [ ] Rollback capabilities

## 📝 Current State

**Current Status**: The project has a complete CLI framework, all CORE_MODELS implemented with Pydantic validation, comprehensive unit testing (360 tests, 74% coverage), dependency resolution, processor module with multicall integration, and change tracking capabilities.

**Development Guidelines**:
- All new features should include documentation updates
- Consider impact on existing CLI interface design
- Ensure new features align with functional programming principles
- Add appropriate error handling and user feedback

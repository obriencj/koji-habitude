# TODO - Future Features

This document tracks planned features and improvements for koji-habitude.

## 🧪 Unit Testing

**Goal**: Comprehensive test coverage for core functionality.

### Data Schema Testing
- [ ] Test YAML loading and validation
- [ ] Test template schema validation
- [ ] Test object data structure validation
- [ ] Test invalid data handling

### Comparison Testing
- [ ] Test koji object diffing logic (once implemented)
- [ ] Test update call generation
- [ ] Test multicall result processing
- [ ] Mock koji responses for testing

### Dependency Resolution Testing
- [ ] Test simple dependency chains
- [ ] Test circular dependency detection
- [ ] Test cross-dependency deferral
- [ ] Test tier generation and ordering
- [ ] Test complex dependency scenarios

### Template Testing
- [ ] Test Jinja2 template expansion
- [ ] Test recursive template processing
- [ ] Test template error handling
- [ ] Test template schema validation

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

- [ ] Web UI for configuration management
- [ ] Integration with git hooks for automatic sync
- [ ] Backup/restore functionality
- [ ] Configuration drift detection
- [ ] Multi-hub synchronization
- [ ] Template marketplace/sharing
- [ ] Performance metrics and monitoring
- [ ] Rollback capabilities
- [ ] Configuration as Code (CaC) integrations

## 📝 Notes

- Maintain backward compatibility when adding new features
- All new features should include documentation updates
- Consider impact on existing CLI interface design
- Ensure new features align with functional programming principles
- Add appropriate error handling and user feedback

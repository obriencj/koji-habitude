# Solver Test Data

This directory contains test data files for testing the dependency resolution solver functionality.

## Test Data Files

### Simple Cases
- **`simple_chain.yaml`** - Linear dependency chain (tag1 -> tag2 -> tag3)
- **`independent_objects.yaml`** - Objects with no dependencies (users, groups, permissions, external repos)
- **`target_dependencies.yaml`** - Target objects with tag dependencies

### Dependency Types
- **`user_group_dependencies.yaml`** - User -> group and user -> permission dependencies
- **`tag_external_repo.yaml`** - Tag -> external repository dependencies
- **`cross_dependencies.yaml`** - Complex cross-dependencies between different object types

### Template-Based
- **`product_template.yaml`** - Template for creating product-based dependency structures
- **`testproduct.yaml`** - Example product using the template (creates complex nested dependencies)

### Edge Cases
- **`missing_dependencies.yaml`** - Objects with dependencies that don't exist (tests MissingObject creation)
- **`circular_dependencies.yaml`** - Simple circular dependency (tag-a -> tag-b -> tag-c -> tag-a)
- **`complex_circular.yaml`** - Multiple overlapping circular dependencies

## Testing Strategy

1. **Start with simple cases** to validate basic functionality
2. **Test each dependency type** individually
3. **Test cross-dependencies** between different object types
4. **Test missing dependencies** to validate MissingObject creation
5. **Test circular dependencies** to validate splitting functionality
6. **Test complex scenarios** with multiple overlapping cycles

## Expected Solver Behavior

- **Simple chains**: Should resolve in dependency order (dependencies first)
- **Independent objects**: Should resolve in any order
- **Missing dependencies**: Should create MissingObject placeholders
- **Circular dependencies**: Should split objects to break cycles
- **Complex scenarios**: Should handle multiple cycles and cross-dependencies

# The end.

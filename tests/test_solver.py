"""
koji-habitude - test_solver

Unit tests for koji_habitude.solver module.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

import unittest
from pathlib import Path
from typing import List, Optional

from koji_habitude.solver import Solver, Node
from koji_habitude.resolver import Resolver
from koji_habitude.namespace import Namespace
from koji_habitude.loader import MultiLoader, YAMLLoader

test_data_path = Path(__file__).parent / 'data' / 'solver'


def load_namespace_from_files(filenames: List[str]) -> Namespace:
    """
    Load YAML files and populate a namespace with the results.

    Args:
        filenames: List of YAML filenames to load from tests/data/solver/

    Returns:
        Namespace populated with objects from the files
    """
    namespace = Namespace()
    loader = MultiLoader([YAMLLoader])

    # Convert filenames to full file paths
    file_paths = []
    for filename in filenames:
        file_path = test_data_path / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Test data file not found: {file_path}")
        file_paths.append(file_path)

    # Load all files at once and feed into namespace
    objects = loader.load(file_paths)
    namespace.feedall_raw(objects)
    namespace.expand()

    return namespace

def create_solver_with_files(filenames: List[str], work_keys: Optional[List[tuple]] = None) -> Solver:
    """
    Create a solver with a namespace populated from the specified files.

    Args:
        filenames: List of YAML filenames to load
        work_keys: Optional list of (type, name) tuples to specify work items.
                    If None, uses all objects from the namespace.

    Returns:
        Solver instance ready for testing
    """
    namespace = load_namespace_from_files(filenames)
    resolver = Resolver(namespace)

    if work_keys is None:
        # Use all objects from the namespace as work items
        work_keys = list(namespace._ns.keys())

    solver = Solver(resolver, work_keys)
    return solver

def get_expected_dependencies(namespace: Namespace, key: tuple) -> List[tuple]:
    """
    Get the expected dependencies for an object in the namespace.

    Args:
        namespace: Namespace containing the object
        key: (type, name) tuple identifying the object

    Returns:
        List of (type, name) dependency tuples
    """
    obj = namespace._ns.get(key)
    if obj is None:
        return []
    return list(obj.dependency_keys())


def assert_dependency_order(test, resolved_objects: List, expected_order: List[tuple]):
    """
    Assert that objects were resolved in the expected dependency order.

    Args:
        resolved_objects: List of resolved objects from solver iteration
        expected_order: List of (type, name) tuples in expected order
    """
    resolved_keys = [obj.key() for obj in resolved_objects]
    test.assertEqual(resolved_keys, expected_order)


def assert_contains_objects(test, resolved_objects: List, expected_keys: List[tuple]):
    """
    Assert that resolved objects contain the expected keys (order doesn't matter).

    Args:
        resolved_objects: List of resolved objects from solver iteration
        expected_keys: List of (type, name) tuples that should be present
    """
    resolved_keys = {obj.key() for obj in resolved_objects}
    expected_set = set(expected_keys)
    test.assertEqual(resolved_keys, expected_set)


class TestSolverBasic(unittest.TestCase):
    """Test basic solver functionality."""

    def test_solver_initialization(self):
        """Test solver initialization with work items."""
        # Create a simple namespace with independent objects
        namespace = load_namespace_from_files(['independent_objects.yaml'])
        resolver = Resolver(namespace)

        # Test initialization with specific work keys
        work_keys = [('user', 'build-user'), ('group', 'packagers')]
        solver = Solver(resolver, work_keys)

        self.assertEqual(solver.resolver, resolver)
        self.assertEqual(solver.work, work_keys)
        self.assertIsNone(solver.remaining)

    def test_solver_initialization_with_all_objects(self):
        """Test solver initialization using all objects from namespace."""
        # Create a namespace with multiple objects
        namespace = load_namespace_from_files(['independent_objects.yaml'])
        resolver = Resolver(namespace)

        # Initialize with all objects as work items
        all_keys = list(namespace._ns.keys())
        solver = Solver(resolver, all_keys)

        self.assertEqual(solver.work, all_keys)
        self.assertGreater(len(solver.work), 0)

    def test_solver_prepare(self):
        """Test solver preparation phase."""
        # Create solver with simple chain data
        solver = create_solver_with_files(['simple_chain.yaml'])

        # Before prepare, remaining should be None
        self.assertIsNone(solver.remaining)

        # Prepare the solver
        solver.prepare()

        # After prepare, remaining should be populated
        self.assertIsNotNone(solver.remaining)
        self.assertIsInstance(solver.remaining, dict)

        # Should have nodes for all work items
        self.assertEqual(len(solver.remaining), len(solver.work))

        # All remaining items should be Node objects
        for key, node in solver.remaining.items():
            self.assertIsInstance(node, Node)
            self.assertEqual(node.key, key)

    def test_solver_prepare_creates_dependency_nodes(self):
        """Test that prepare() creates nodes for dependencies not in work list."""
        # Create solver with simple chain (tag1 -> tag2 -> tag3)
        solver = create_solver_with_files(['simple_chain.yaml'])

        # Only include tag1 in work list
        work_keys = [('tag', 'tag1')]
        solver.work = work_keys
        solver.remaining = None

        solver.prepare()

        # Should have nodes for tag1, tag2, and tag3 (dependencies)
        expected_keys = {('tag', 'tag1'), ('tag', 'tag2'), ('tag', 'tag3')}
        actual_keys = set(solver.remaining.keys())
        self.assertEqual(actual_keys, expected_keys)

    def test_remaining_keys_before_prepare(self):
        """Test remaining_keys() raises error before prepare()."""
        solver = create_solver_with_files(['independent_objects.yaml'])

        with self.assertRaises(ValueError) as context:
            solver.remaining_keys()

        self.assertIn("Solver not prepared", str(context.exception))

    def test_remaining_keys_after_prepare(self):
        """Test remaining_keys() returns correct keys after prepare()."""
        solver = create_solver_with_files(['simple_chain.yaml'])
        solver.prepare()

        remaining = solver.remaining_keys()

        self.assertIsInstance(remaining, set)
        self.assertEqual(len(remaining), len(solver.remaining))

        # Should contain all the work keys
        work_set = set(solver.work)
        self.assertTrue(work_set.issubset(remaining))

    def test_remaining_keys_updates_during_iteration(self):
        """Test that remaining_keys() updates as objects are processed."""
        solver = create_solver_with_files(['simple_chain.yaml'])
        solver.prepare()

        initial_count = len(solver.remaining_keys())
        self.assertGreater(initial_count, 0)

        # Process one object
        resolved_objects = list(solver)

        # After iteration, remaining should be empty
        final_count = len(solver.remaining_keys())
        self.assertEqual(final_count, 0)

    def test_solver_report_before_prepare(self):
        """Test solver report before prepare() raises error."""
        solver = create_solver_with_files(['independent_objects.yaml'])

        with self.assertRaises(ValueError) as context:
            solver.report()

        self.assertIn("Solver not prepared", str(context.exception))

    def test_solver_report_after_prepare(self):
        """Test solver report after prepare()."""
        solver = create_solver_with_files(['independent_objects.yaml'])
        solver.prepare()

        report = solver.report()

        # Should return a report from the resolver
        self.assertIsNotNone(report)
        self.assertIsInstance(report.missing, list)

    def test_solver_report_with_missing_dependencies(self):
        """Test solver report when there are missing dependencies."""
        solver = create_solver_with_files(['missing_dependencies.yaml'])
        solver.prepare()

        report = solver.report()

        # Should report missing dependencies
        self.assertGreater(len(report.missing), 0)

        # Should contain expected missing dependencies
        missing_keys = set(report.missing)
        expected_missing = {
            ('tag', 'missing-parent-tag'),
            ('tag', 'missing-build-tag'),
            ('tag', 'missing-dest-tag'),
            ('group', 'missing-group'),
            ('permission', 'missing-permission'),
            ('external-repo', 'missing-external-repo')
        }

        # Should contain at least some of the expected missing dependencies
        self.assertTrue(missing_keys.intersection(expected_missing))

    def test_solver_prepare_calls_resolver_prepare(self):
        """Test that solver.prepare() calls resolver.prepare()."""
        # Create a mock resolver to verify prepare() is called
        namespace = load_namespace_from_files(['independent_objects.yaml'])
        resolver = Resolver(namespace)

        # Mock the resolver's prepare method
        original_prepare = resolver.prepare
        prepare_called = False

        def mock_prepare():
            nonlocal prepare_called
            prepare_called = True
            return original_prepare()

        resolver.prepare = mock_prepare

        solver = Solver(resolver, [('user', 'build-user')])
        solver.prepare()

        self.assertTrue(prepare_called)


class TestSolverSimpleChains(unittest.TestCase):
    """Test solver with simple dependency chains."""

    def test_simple_linear_chain(self):
        """Test solver with simple linear dependency chain."""
        # Create solver with simple chain (tag1 -> tag2 -> tag3)
        solver = create_solver_with_files(['simple_chain.yaml'])
        solver.prepare()

        # Resolve all objects
        resolved_objects = list(solver)

        # Should resolve in dependency order: tag3, tag2, tag1
        expected_order = [
            ('tag', 'tag3'),
            ('tag', 'tag2'),
            ('tag', 'tag1')
        ]
        assert_dependency_order(self, resolved_objects, expected_order)

        # After resolution, remaining should be empty
        self.assertEqual(len(solver.remaining_keys()), 0)

    def test_simple_linear_chain_partial_work(self):
        """Test solver with partial work list on linear chain."""
        # Create solver but only include tag1 in work list
        solver = create_solver_with_files(['simple_chain.yaml'], work_keys=[('tag', 'tag1')])
        solver.prepare()

        # Should still resolve all dependencies
        resolved_objects = list(solver)

        # Should resolve in dependency order: tag3, tag2, tag1
        expected_order = [
            ('tag', 'tag3'),
            ('tag', 'tag2'),
            ('tag', 'tag1')
        ]
        assert_dependency_order(self, resolved_objects, expected_order)

    def test_independent_objects(self):
        """Test solver with objects that have no dependencies."""
        solver = create_solver_with_files(['independent_objects.yaml'])
        solver.prepare()

        # Resolve all objects
        resolved_objects = list(solver)

        # Should contain all objects from the file, plus the implicit missing permissions
        # for the packagers group
        expected_keys = [
            ('user', 'build-user'),
            ('user', 'release-user'),
            ('group', 'packagers'),
            ('permission', 'admin'),
            ('external-repo', 'epel-9'),
            ('permission', 'pkglist'),
            ('permission', 'taggers'),
        ]
        assert_contains_objects(self, resolved_objects, expected_keys)

        # Order doesn't matter for independent objects, but all should be resolved
        self.assertEqual(len(resolved_objects), len(expected_keys))

    def test_independent_objects_partial_work(self):
        """Test solver with partial work list on independent objects."""
        # Only include some objects in work list
        work_keys = [('user', 'build-user'), ('group', 'packagers')]
        solver = create_solver_with_files(['independent_objects.yaml'], work_keys=work_keys)
        solver.prepare()

        # Resolve objects
        resolved_objects = list(solver)

        # Should only resolve the work items
        expected_keys = [
            ('user', 'build-user'),
            ('group', 'packagers'),
            ('permission', 'pkglist'),
            ('permission', 'taggers'),
        ]
        assert_contains_objects(self, resolved_objects, expected_keys)
        self.assertEqual(len(resolved_objects), 4)

    def test_target_dependencies(self):
        """Test solver with target -> tag dependencies."""
        solver = create_solver_with_files(['target_dependencies.yaml'])
        solver.prepare()

        # Resolve all objects
        resolved_objects = list(solver)

        # Should resolve tags first, then targets
        # Tags have no dependencies, targets depend on tags
        tag_keys = [('tag', 'build-tag'), ('tag', 'dest-tag')]
        target_keys = [('target', 'myproject-build'), ('target', 'myproject-release')]

        # Find positions of tags and targets
        resolved_keys = [obj.key() for obj in resolved_objects]
        tag_positions = [resolved_keys.index(key) for key in tag_keys if key in resolved_keys]
        target_positions = [resolved_keys.index(key) for key in target_keys if key in resolved_keys]

        # All tags should come before all targets
        if tag_positions and target_positions:
            max_tag_pos = max(tag_positions)
            min_target_pos = min(target_positions)
            self.assertLess(max_tag_pos, min_target_pos,
                           "Tags should be resolved before targets")

    def test_target_dependencies_partial_work(self):
        """Test solver with partial work list on target dependencies."""
        # Only include targets in work list
        work_keys = [('target', 'myproject-build'), ('target', 'myproject-release')]
        solver = create_solver_with_files(['target_dependencies.yaml'], work_keys=work_keys)
        solver.prepare()

        # Resolve objects
        resolved_objects = list(solver)

        # Should resolve all tags (dependencies) and the requested targets
        expected_keys = [
            ('tag', 'build-tag'),
            ('tag', 'dest-tag'),
            ('target', 'myproject-build'),
            ('target', 'myproject-release')
        ]
        assert_contains_objects(self, resolved_objects, expected_keys)

        # Tags should still come before targets
        resolved_keys = [obj.key() for obj in resolved_objects]
        tag_positions = [resolved_keys.index(key) for key in [('tag', 'build-tag'), ('tag', 'dest-tag')]]
        target_positions = [resolved_keys.index(key) for key in [('target', 'myproject-build'), ('target', 'myproject-release')]]

        if tag_positions and target_positions:
            max_tag_pos = max(tag_positions)
            min_target_pos = min(target_positions)
            self.assertLess(max_tag_pos, min_target_pos)

    def test_empty_work_list(self):
        """Test solver with empty work list."""
        solver = create_solver_with_files(['simple_chain.yaml'], work_keys=[])
        solver.prepare()

        # Should have no remaining items
        self.assertEqual(len(solver.remaining_keys()), 0)

        # Should resolve nothing
        resolved_objects = list(solver)
        self.assertEqual(len(resolved_objects), 0)

    def test_single_object_work_list(self):
        """Test solver with single object in work list."""
        work_keys = [('tag', 'tag3')]  # Leaf node with no dependencies
        solver = create_solver_with_files(['simple_chain.yaml'], work_keys=work_keys)
        solver.prepare()

        # Should resolve only the single object
        resolved_objects = list(solver)
        self.assertEqual(len(resolved_objects), 1)
        self.assertEqual(resolved_objects[0].key(), ('tag', 'tag3'))


class TestSolverDependencyTypes(unittest.TestCase):
    """Test solver with different types of dependencies."""

    def test_user_group_dependencies(self):
        """Test solver with user -> group dependencies."""
        solver = create_solver_with_files(['user_group_dependencies.yaml'])
        solver.prepare()

        # Resolve all objects
        resolved_objects = list(solver)

        # Should contain all objects from the file
        expected_keys = [
            ('group', 'packagers'),
            ('group', 'release-team'),
            ('permission', 'admin'),
            ('user', 'packager1'),
            ('user', 'packager2'),
            ('user', 'release-manager'),
            # Implicit missing permissions
            ('permission', 'pkglist'),
            ('permission', 'taggers'),
            ('permission', 'release'),
            ('permission', 'sign')
        ]
        assert_contains_objects(self, resolved_objects, expected_keys)

        # Groups and permissions should be resolved before users
        resolved_keys = [obj.key() for obj in resolved_objects]
        group_positions = [resolved_keys.index(key) for key in [('group', 'packagers'), ('group', 'release-team')] if key in resolved_keys]
        user_positions = [resolved_keys.index(key) for key in [('user', 'packager1'), ('user', 'packager2'), ('user', 'release-manager')] if key in resolved_keys]

        if group_positions and user_positions:
            max_group_pos = max(group_positions)
            min_user_pos = min(user_positions)
            self.assertLess(max_group_pos, min_user_pos,
                           "Groups should be resolved before users")

    def test_user_group_dependencies_partial_work(self):
        """Test solver with partial work list on user-group dependencies."""
        # Only include users in work list
        work_keys = [('user', 'packager1'), ('user', 'release-manager')]
        solver = create_solver_with_files(['user_group_dependencies.yaml'], work_keys=work_keys)
        solver.prepare()

        # Resolve objects
        resolved_objects = list(solver)

        # Should resolve dependencies (groups, permissions) and requested users
        expected_keys = [
            ('group', 'packagers'),
            ('group', 'release-team'),
            ('permission', 'admin'),
            ('user', 'packager1'),
            ('user', 'release-manager'),
            # Implicit missing permissions
            ('permission', 'pkglist'),
            ('permission', 'taggers'),
            ('permission', 'release'),
            ('permission', 'sign')
        ]
        assert_contains_objects(self, resolved_objects, expected_keys)

    def test_tag_external_repo_dependencies(self):
        """Test solver with tag -> external-repo dependencies."""
        solver = create_solver_with_files(['tag_external_repo.yaml'])
        solver.prepare()

        # Resolve all objects
        resolved_objects = list(solver)

        # Should contain all objects from the file
        expected_keys = [
            ('external-repo', 'epel-9'),
            ('external-repo', 'rpmfusion-free'),
            ('tag', 'myproject-base'),
            ('tag', 'myproject-build')
        ]
        assert_contains_objects(self, resolved_objects, expected_keys)

        # External repos should be resolved before tags that depend on them
        resolved_keys = [obj.key() for obj in resolved_objects]
        repo_positions = [resolved_keys.index(key) for key in [('external-repo', 'epel-9'), ('external-repo', 'rpmfusion-free')] if key in resolved_keys]
        tag_positions = [resolved_keys.index(key) for key in [('tag', 'myproject-base'), ('tag', 'myproject-build')] if key in resolved_keys]

        if repo_positions and tag_positions:
            max_repo_pos = max(repo_positions)
            min_tag_pos = min(tag_positions)
            self.assertLess(max_repo_pos, min_tag_pos,
                           "External repos should be resolved before tags")

    def test_tag_external_repo_dependencies_partial_work(self):
        """Test solver with partial work list on tag-external-repo dependencies."""
        # Only include tags in work list
        work_keys = [('tag', 'myproject-build')]
        solver = create_solver_with_files(['tag_external_repo.yaml'], work_keys=work_keys)
        solver.prepare()

        # Resolve objects
        resolved_objects = list(solver)

        # Should resolve all dependencies and the requested tag
        expected_keys = [
            ('external-repo', 'epel-9'),
            ('external-repo', 'rpmfusion-free'),
            ('tag', 'myproject-base'),
            ('tag', 'myproject-build')
        ]
        assert_contains_objects(self, resolved_objects, expected_keys)

    def test_cross_dependencies(self):
        """Test solver with cross-dependencies between object types."""
        solver = create_solver_with_files(['cross_dependencies.yaml'])
        solver.prepare()

        # Resolve all objects
        resolved_objects = list(solver)

        # Should contain all objects from the file
        expected_keys = [
            ('group', 'packagers'),
            ('user', 'packager1'),
            ('tag', 'base-tag'),
            ('tag', 'build-tag'),
            ('target', 'myproject-build'),
            ('external-repo', 'epel-9'),
            ('tag', 'myproject-with-repo'),
            # Implicit missing permissions
            ('permission', 'pkglist'),
            ('permission', 'taggers')
        ]
        assert_contains_objects(self, resolved_objects, expected_keys)

        # Verify dependency order across different object types
        resolved_keys = [obj.key() for obj in resolved_objects]

        # Groups should come before users
        group_pos = resolved_keys.index(('group', 'packagers'))
        user_pos = resolved_keys.index(('user', 'packager1'))
        self.assertLess(group_pos, user_pos, "Groups should come before users")

        # Base tag should come before build tag
        base_tag_pos = resolved_keys.index(('tag', 'base-tag'))
        build_tag_pos = resolved_keys.index(('tag', 'build-tag'))
        self.assertLess(base_tag_pos, build_tag_pos, "Base tag should come before build tag")

        # Tags should come before targets
        tag_positions = [resolved_keys.index(key) for key in [('tag', 'base-tag'), ('tag', 'build-tag')]]
        target_positions = [resolved_keys.index(key) for key in [('target', 'myproject-build')]]
        max_tag_pos = max(tag_positions)
        min_target_pos = min(target_positions)
        self.assertLess(max_tag_pos, min_target_pos, "Tags should come before targets")

        # External repo should come before tag that uses it
        repo_pos = resolved_keys.index(('external-repo', 'epel-9'))
        tag_with_repo_pos = resolved_keys.index(('tag', 'myproject-with-repo'))
        self.assertLess(repo_pos, tag_with_repo_pos, "External repo should come before tag that uses it")

    def test_cross_dependencies_partial_work(self):
        """Test solver with partial work list on cross-dependencies."""
        # Only include targets and the tag with external repo
        work_keys = [('target', 'myproject-build'), ('tag', 'myproject-with-repo')]
        solver = create_solver_with_files(['cross_dependencies.yaml'], work_keys=work_keys)
        solver.prepare()

        # Resolve objects
        resolved_objects = list(solver)

        # Should resolve all dependencies and the requested objects
        expected_keys = [
            ('tag', 'base-tag'),
            ('tag', 'build-tag'),
            ('target', 'myproject-build'),
            ('external-repo', 'epel-9'),
            ('tag', 'myproject-with-repo')
        ]
        assert_contains_objects(self, resolved_objects, expected_keys)

    def test_mixed_dependency_types(self):
        """Test solver with multiple different dependency types in one scenario."""
        # Use multiple files to create a complex scenario
        solver = create_solver_with_files([
            'user_group_dependencies.yaml',
            'tag_external_repo.yaml'
        ])
        solver.prepare()

        # Resolve all objects
        resolved_objects = list(solver)

        # Should contain objects from both files
        expected_keys = [
            # From user_group_dependencies.yaml
            ('group', 'packagers'),
            ('group', 'release-team'),
            ('permission', 'admin'),
            ('user', 'packager1'),
            ('user', 'packager2'),
            ('user', 'release-manager'),
            # From tag_external_repo.yaml
            ('external-repo', 'epel-9'),
            ('external-repo', 'rpmfusion-free'),
            ('tag', 'myproject-base'),
            ('tag', 'myproject-build'),
            # Implicit missing permissions
            ('permission', 'pkglist'),
            ('permission', 'taggers'),
            ('permission', 'release'),
            ('permission', 'sign')
        ]
        assert_contains_objects(self, resolved_objects, expected_keys)

        # Verify that dependency order is maintained across different types
        resolved_keys = [obj.key() for obj in resolved_objects]

        # Groups should come before users
        group_pos = resolved_keys.index(('group', 'packagers'))
        user_pos = resolved_keys.index(('user', 'packager1'))
        self.assertLess(group_pos, user_pos)

        # External repos should come before tags
        repo_pos = resolved_keys.index(('external-repo', 'epel-9'))
        tag_pos = resolved_keys.index(('tag', 'myproject-base'))
        self.assertLess(repo_pos, tag_pos)


class TestSolverMissingDependencies(unittest.TestCase):
    """Test solver with missing dependencies."""

    def test_missing_dependencies(self):
        """Test solver with objects that have missing dependencies."""
        # TODO: Implement test using missing_dependencies.yaml
        pass

    def test_missing_dependency_reporting(self):
        """Test that missing dependencies are properly reported."""
        # TODO: Implement test
        pass


class TestSolverCircularDependencies(unittest.TestCase):
    """Test solver with circular dependencies."""

    def test_simple_circular_dependency(self):
        """Test solver with simple circular dependency."""
        # TODO: Implement test using circular_dependencies.yaml
        pass

    def test_complex_circular_dependencies(self):
        """Test solver with complex overlapping circular dependencies."""
        # TODO: Implement test using complex_circular.yaml
        pass

    def test_circular_dependency_splitting(self):
        """Test that circular dependencies trigger splitting."""
        # TODO: Implement test
        pass


class TestSolverTemplates(unittest.TestCase):
    """Test solver with template-based data."""

    def test_template_based_dependencies(self):
        """Test solver with template-generated dependencies."""
        # TODO: Implement test using product_template.yaml and testproduct.yaml
        pass


class TestSolverIntegration(unittest.TestCase):
    """Test solver integration scenarios."""

    def test_mixed_scenario(self):
        """Test solver with mixed dependency scenarios."""
        # TODO: Implement test using multiple files
        pass

    def test_large_dependency_graph(self):
        """Test solver with large, complex dependency graph."""
        # TODO: Implement test
        pass


# The end.

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
        # TODO: Implement test using simple_chain.yaml
        pass

    def test_independent_objects(self):
        """Test solver with objects that have no dependencies."""
        # TODO: Implement test using independent_objects.yaml
        pass

    def test_target_dependencies(self):
        """Test solver with target -> tag dependencies."""
        # TODO: Implement test using target_dependencies.yaml
        pass


class TestSolverDependencyTypes(unittest.TestCase):
    """Test solver with different types of dependencies."""

    def test_user_group_dependencies(self):
        """Test solver with user -> group dependencies."""
        # TODO: Implement test using user_group_dependencies.yaml
        pass

    def test_tag_external_repo_dependencies(self):
        """Test solver with tag -> external-repo dependencies."""
        # TODO: Implement test using tag_external_repo.yaml
        pass

    def test_cross_dependencies(self):
        """Test solver with cross-dependencies between object types."""
        # TODO: Implement test using cross_dependencies.yaml
        pass


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

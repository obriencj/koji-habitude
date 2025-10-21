"""
koji-habitude - test_solver

Unit tests for koji_habitude.solver module.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated

import unittest
from pathlib import Path
from typing import List, Optional

from koji_habitude.solver import Solver, Node
from koji_habitude.resolver import Resolver
from koji_habitude.namespace import Namespace, Redefine
from koji_habitude.loader import MultiLoader, YAMLLoader

test_data_path = Path(__file__).parent / 'data' / 'solver'


def load_namespace_from_files(
    filenames: List[str],
    redefine: Redefine = Redefine.ERROR) -> Namespace:
    """
    Load YAML files and populate a namespace with the results.

    Args:
        filenames: List of YAML filenames to load from tests/data/solver/

    Returns:
        Namespace populated with objects from the files
    """
    namespace = Namespace(redefine=redefine)
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

def create_solver_with_files(
    filenames: List[str],
    work_keys: Optional[List[tuple]] = None,
    redefine: Redefine = Redefine.ERROR) -> Solver:
    """
    Create a solver with a namespace populated from the specified files.

    Args:
        filenames: List of YAML filenames to load
        work_keys: Optional list of (type, name) tuples to specify work items.
                    If None, uses all objects from the namespace.

    Returns:
        Solver instance ready for testing
    """
    namespace = load_namespace_from_files(filenames, redefine=redefine)
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
        self.assertIsInstance(report.phantoms, dict)

    def test_solver_report_with_missing_dependencies(self):
        """Test solver report when there are missing dependencies."""
        solver = create_solver_with_files(['missing_dependencies.yaml'])
        solver.prepare()

        report = solver.report()

        # Should report missing dependencies
        self.assertGreater(len(report.phantoms), 0)

        # Should contain expected missing dependencies
        missing_keys = set(report.phantoms)
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
        solver = create_solver_with_files(['missing_dependencies.yaml'])
        solver.prepare()

        # Resolve all objects
        resolved_objects = list(solver)

        # Should contain all objects from the file plus MissingObjects
        expected_keys = [
            # Objects from the YAML file
            ('tag', 'child-tag'),
            ('target', 'missing-target'),
            ('user', 'user-with-missing-group'),
            ('tag', 'tag-with-missing-repo'),
            # Missing dependencies that should be created as MissingObjects
            ('tag', 'missing-parent-tag'),
            ('tag', 'missing-build-tag'),
            ('tag', 'missing-dest-tag'),
            ('group', 'missing-group'),
            ('permission', 'missing-permission'),
            ('external-repo', 'missing-external-repo')
        ]
        assert_contains_objects(self, resolved_objects, expected_keys)

        # MissingObjects should be resolved before objects that depend on them
        resolved_keys = [obj.key() for obj in resolved_objects]

        # Find positions of missing objects and their dependents
        missing_parent_pos = resolved_keys.index(('tag', 'missing-parent-tag'))
        child_tag_pos = resolved_keys.index(('tag', 'child-tag'))
        self.assertLess(missing_parent_pos, child_tag_pos,
                       "Missing parent should be resolved before child tag")

        # Missing build/dest tags should come before target
        missing_build_pos = resolved_keys.index(('tag', 'missing-build-tag'))
        missing_dest_pos = resolved_keys.index(('tag', 'missing-dest-tag'))
        target_pos = resolved_keys.index(('target', 'missing-target'))
        self.assertLess(missing_build_pos, target_pos,
                       "Missing build tag should come before target")
        self.assertLess(missing_dest_pos, target_pos,
                       "Missing dest tag should come before target")

        # Missing group should come before user
        missing_group_pos = resolved_keys.index(('group', 'missing-group'))
        user_pos = resolved_keys.index(('user', 'user-with-missing-group'))
        self.assertLess(missing_group_pos, user_pos,
                       "Missing group should come before user")

    def test_missing_dependencies_partial_work(self):
        """Test solver with partial work list on missing dependencies."""
        # Only include some objects in work list
        work_keys = [('tag', 'child-tag'), ('user', 'user-with-missing-group')]
        solver = create_solver_with_files(['missing_dependencies.yaml'], work_keys=work_keys)
        solver.prepare()

        # Resolve objects
        resolved_objects = list(solver)

        # Should resolve the work items and their missing dependencies
        expected_keys = [
            # Work items
            ('tag', 'child-tag'),
            ('user', 'user-with-missing-group'),
            # Missing dependencies for the work items
            ('tag', 'missing-parent-tag'),
            ('group', 'missing-group'),
            ('permission', 'missing-permission')
        ]
        assert_contains_objects(self, resolved_objects, expected_keys)

        # Should not resolve objects not in work list
        resolved_keys = [obj.key() for obj in resolved_objects]
        self.assertNotIn(('target', 'missing-target'), resolved_keys)
        self.assertNotIn(('tag', 'tag-with-missing-repo'), resolved_keys)

    def test_missing_dependency_reporting(self):
        """Test that missing dependencies are properly reported."""
        solver = create_solver_with_files(['missing_dependencies.yaml'])
        solver.prepare()

        # Get the report before resolving
        report = solver.report()

        # Should report all missing dependencies
        expected_missing = {
            ('tag', 'missing-parent-tag'),
            ('tag', 'missing-build-tag'),
            ('tag', 'missing-dest-tag'),
            ('group', 'missing-group'),
            ('permission', 'missing-permission'),
            ('external-repo', 'missing-external-repo')
        }

        missing_set = set(report.phantoms)
        self.assertEqual(missing_set, expected_missing)

        # After resolving, the report should still show the same missing dependencies
        resolved_objects = list(solver)
        report_after = solver.report()

        self.assertEqual(set(report_after.phantoms), expected_missing)

    def test_missing_dependencies_no_failure(self):
        """Test that missing dependencies don't cause solver to fail."""
        solver = create_solver_with_files(['missing_dependencies.yaml'])
        solver.prepare()

        # Should be able to iterate through all objects without failure
        resolved_objects = list(solver)

        # Should have resolved all objects (including MissingObjects)
        self.assertGreater(len(resolved_objects), 0)

        # Should have no remaining items
        self.assertEqual(len(solver.remaining_keys()), 0)

    def test_missing_dependencies_ordering(self):
        """Test that missing dependencies are resolved in correct order."""
        solver = create_solver_with_files(['missing_dependencies.yaml'])
        solver.prepare()

        # Resolve objects
        resolved_objects = list(solver)
        resolved_keys = [obj.key() for obj in resolved_objects]

        # All missing dependencies should be resolved before their dependents
        missing_deps = [
            ('tag', 'missing-parent-tag'),
            ('tag', 'missing-build-tag'),
            ('tag', 'missing-dest-tag'),
            ('group', 'missing-group'),
            ('permission', 'missing-permission'),
            ('external-repo', 'missing-external-repo')
        ]

        dependents = [
            ('tag', 'child-tag'),
            ('target', 'missing-target'),
            ('user', 'user-with-missing-group'),
            ('tag', 'tag-with-missing-repo')
        ]

        # Find positions
        missing_positions = [resolved_keys.index(key) for key in missing_deps]
        dependent_positions = [resolved_keys.index(key) for key in dependents]

        # All missing dependencies should come before all dependents
        max_missing_pos = max(missing_positions)
        min_dependent_pos = min(dependent_positions)
        self.assertLess(max_missing_pos, min_dependent_pos,
                       "All missing dependencies should be resolved before their dependents")

    def test_missing_dependencies_with_existing_objects(self):
        """Test missing dependencies mixed with existing objects."""
        # Use multiple files to create a scenario with both existing and missing dependencies
        solver = create_solver_with_files([
            'simple_chain.yaml',
            'missing_dependencies.yaml'
        ])
        solver.prepare()

        # Resolve objects
        resolved_objects = list(solver)

        # Should contain objects from both files
        expected_keys = [
            # From simple_chain.yaml
            ('tag', 'tag1'),
            ('tag', 'tag2'),
            ('tag', 'tag3'),
            # From missing_dependencies.yaml
            ('tag', 'child-tag'),
            ('target', 'missing-target'),
            ('user', 'user-with-missing-group'),
            ('tag', 'tag-with-missing-repo'),
            # Missing dependencies
            ('tag', 'missing-parent-tag'),
            ('tag', 'missing-build-tag'),
            ('tag', 'missing-dest-tag'),
            ('group', 'missing-group'),
            ('permission', 'missing-permission'),
            ('external-repo', 'missing-external-repo')
        ]
        assert_contains_objects(self, resolved_objects, expected_keys)

        # Verify that dependency order is maintained across existing and missing objects
        resolved_keys = [obj.key() for obj in resolved_objects]

        # Simple chain should maintain its order
        tag3_pos = resolved_keys.index(('tag', 'tag3'))
        tag2_pos = resolved_keys.index(('tag', 'tag2'))
        tag1_pos = resolved_keys.index(('tag', 'tag1'))
        self.assertLess(tag3_pos, tag2_pos)
        self.assertLess(tag2_pos, tag1_pos)

        # Missing dependencies should come before their dependents
        missing_parent_pos = resolved_keys.index(('tag', 'missing-parent-tag'))
        child_tag_pos = resolved_keys.index(('tag', 'child-tag'))
        self.assertLess(missing_parent_pos, child_tag_pos)


class TestSolverCircularDependencies(unittest.TestCase):
    """Test solver with circular dependencies."""

    def test_simple_circular_dependency(self):
        """Test solver with simple circular dependency."""
        solver = create_solver_with_files(['circular_dependencies.yaml'])
        solver.prepare()

        # Resolve all objects
        resolved_objects = list(solver)

        # Should contain all objects from the file
        expected_keys = [
            ('tag-split', 'tag-a'),
            ('tag', 'tag-a'),
            ('tag', 'tag-b'),
            ('tag', 'tag-c')
        ]
        assert_contains_objects(self, resolved_objects, expected_keys)

        # Should have resolved all objects without getting stuck
        self.assertEqual(len(resolved_objects), 4)

        # Should have no remaining items
        self.assertEqual(len(solver.remaining_keys()), 0)

        # The circular dependency should have been broken by splitting
        # At least one of the tags should have been split
        # We can't predict which one, but the solver should have handled it

    def test_simple_circular_dependency_partial_work(self):
        """Test solver with partial work list on circular dependency."""
        # Only include one tag in work list
        work_keys = [('tag', 'tag-a')]
        solver = create_solver_with_files(['circular_dependencies.yaml'], work_keys=work_keys)
        solver.prepare()

        # Resolve objects
        resolved_objects = list(solver)

        # Should resolve all tags in the circular dependency
        expected_keys = [
            ('tag-split', 'tag-a'),
            ('tag', 'tag-a'),
            ('tag', 'tag-b'),
            ('tag', 'tag-c')
        ]
        assert_contains_objects(self, resolved_objects, expected_keys)

        # Should have resolved all objects
        self.assertEqual(len(resolved_objects), 4)

    def test_complex_circular_dependencies(self):
        """Test solver with complex overlapping circular dependencies."""
        solver = create_solver_with_files(['complex_circular.yaml'])
        solver.prepare()

        # Resolve all objects
        resolved_objects = list(solver)

        # Should contain all objects from the file
        expected_keys = [
            ('tag-split', 'tag-1'),
            ('tag-split', 'tag-4'),
            ('tag', 'base-tag'),
            ('tag', 'tag-1'),
            ('tag', 'tag-2'),
            ('tag', 'tag-3'),
            ('tag', 'tag-4'),
            ('tag', 'tag-5')
        ]
        assert_contains_objects(self, resolved_objects, expected_keys)

        # Should have resolved all objects without getting stuck
        # 1 for the base tag, score 0
        # 3 from the first loop, plus 1 to break it with a split
        # 2 from the second loop, plus 1 to break it with a split
        self.assertEqual(len(resolved_objects), 8)

        # Should have no remaining items
        self.assertEqual(len(solver.remaining_keys()), 0)

        # Verify that base-tag was resolved first (it has no dependencies)
        resolved_keys = [obj.key() for obj in resolved_objects]
        base_tag_pos = resolved_keys.index(('tag', 'base-tag'))

        # Base tag should be resolved early (it has no dependencies)
        self.assertLess(base_tag_pos, 3, "Base tag should be resolved early")

    def test_complex_circular_dependencies_partial_work(self):
        """Test solver with partial work list on complex circular dependencies."""
        # Only include some tags in work list
        work_keys = [('tag', 'tag-1'), ('tag', 'tag-4')]
        solver = create_solver_with_files(['complex_circular.yaml'], work_keys=work_keys)
        solver.prepare()

        # Resolve objects
        resolved_objects = list(solver)

        # Should resolve all tags in the circular dependencies
        expected_keys = [
            ('tag-split', 'tag-1'),
            ('tag-split', 'tag-4'),
            ('tag', 'base-tag'),
            ('tag', 'tag-1'),
            ('tag', 'tag-2'),
            ('tag', 'tag-3'),
            ('tag', 'tag-4'),
            ('tag', 'tag-5')
        ]
        assert_contains_objects(self, resolved_objects, expected_keys)

        # Should have resolved all objects without getting stuck
        # 1 for the base tag, score 0
        # 3 from the first loop, plus 1 to break it with a split
        # 2 from the second loop, plus 1 to break it with a split
        self.assertEqual(len(resolved_objects), 8)

    def test_circular_dependency_splitting(self):
        """Test that circular dependencies trigger splitting."""
        solver = create_solver_with_files(['circular_dependencies.yaml'])
        solver.prepare()

        # Before resolving, check that tags can be split
        tag_a_key = ('tag', 'tag-a')
        tag_b_key = ('tag', 'tag-b')
        tag_c_key = ('tag', 'tag-c')

        # All tags should be splittable
        self.assertTrue(solver.resolver.resolve(tag_a_key).can_split())
        self.assertTrue(solver.resolver.resolve(tag_b_key).can_split())
        self.assertTrue(solver.resolver.resolve(tag_c_key).can_split())

        # Resolve objects
        resolved_objects = list(solver)

        # Should have resolved all objects plus one split object
        self.assertEqual(len(resolved_objects), 4)

        # The solver should have successfully broken the circular dependency
        # by splitting one of the tags

    def test_circular_dependency_no_splittable_objects(self):
        """Test solver behavior when circular dependency has no splittable objects."""
        # Create a custom scenario with non-splittable objects in a cycle
        # This should cause the solver to fail or get stuck
        solver = create_solver_with_files(['circular_dependencies.yaml'])
        solver.prepare()

        # Mock the tags to be non-splittable
        for key in [('tag', 'tag-a'), ('tag', 'tag-b'), ('tag', 'tag-c')]:
            if key in solver.remaining:
                solver.remaining[key].can_split = False

        # This should raise an error when trying to resolve
        with self.assertRaises(ValueError) as context:
            list(solver)

        self.assertIn("Stuck in a loop", str(context.exception))

    def test_circular_dependency_with_missing_dependencies(self):
        """Test circular dependencies mixed with missing dependencies."""
        # Use multiple files to create a complex scenario
        solver = create_solver_with_files([
            'circular_dependencies.yaml',
            'missing_dependencies.yaml'
        ])
        solver.prepare()

        # Resolve objects
        resolved_objects = list(solver)

        # Should contain objects from both files
        expected_keys = [
            # From circular_dependencies.yaml
            ('tag-split', 'tag-a'),
            ('tag', 'tag-a'),
            ('tag', 'tag-b'),
            ('tag', 'tag-c'),
            # From missing_dependencies.yaml
            ('tag', 'child-tag'),
            ('target', 'missing-target'),
            ('user', 'user-with-missing-group'),
            ('tag', 'tag-with-missing-repo'),
            # Missing dependencies
            ('tag', 'missing-parent-tag'),
            ('tag', 'missing-build-tag'),
            ('tag', 'missing-dest-tag'),
            ('group', 'missing-group'),
            ('permission', 'missing-permission'),
            ('external-repo', 'missing-external-repo')
        ]
        assert_contains_objects(self, resolved_objects, expected_keys)

        # 3 from circular_dependencies.yaml
        # + 1 split object from circular_dependencies.yaml
        # + 4 from missing_dependencies.yaml
        # + 6 implicit missing items
        self.assertEqual(len(resolved_objects), 14)

        # Missing dependencies should be resolved before their dependents
        resolved_keys = [obj.key() for obj in resolved_objects]
        missing_parent_pos = resolved_keys.index(('tag', 'missing-parent-tag'))
        child_tag_pos = resolved_keys.index(('tag', 'child-tag'))
        self.assertLess(missing_parent_pos, child_tag_pos)

    def test_circular_dependency_ordering(self):
        """Test that circular dependencies are resolved in some valid order."""
        solver = create_solver_with_files(['circular_dependencies.yaml'])
        solver.prepare()

        # Resolve objects
        resolved_objects = list(solver)
        resolved_keys = [obj.key() for obj in resolved_objects]

        # All three tags should be resolved
        self.assertIn(('tag', 'tag-a'), resolved_keys)
        self.assertIn(('tag', 'tag-b'), resolved_keys)
        self.assertIn(('tag', 'tag-c'), resolved_keys)

        # The exact order doesn't matter for circular dependencies,
        # but the solver should have successfully broken the cycle
        # and resolved all objects

    def test_circular_dependency_reporting(self):
        """Test that circular dependencies don't affect missing dependency reporting."""
        solver = create_solver_with_files(['circular_dependencies.yaml'])
        solver.prepare()

        # Should have no missing dependencies in this file
        report = solver.report()
        self.assertEqual(len(report.phantoms), 0)

        # After resolving, should still have no missing dependencies
        resolved_objects = list(solver)
        report_after = solver.report()
        self.assertEqual(len(report_after.phantoms), 0)


class TestSolverTemplates(unittest.TestCase):
    """Test solver with template-based data."""

    def test_template_based_dependencies(self):
        """Test solver with template-generated dependencies."""
        solver = create_solver_with_files(['product_template.yaml', 'testproduct.yaml'])
        solver.prepare()

        # Resolve all objects
        resolved_objects = list(solver)

        # Should contain objects generated from the template
        expected_keys = [
            # From product template
            ('group', 'testproduct-packagers'),
            # From testproduct versions
            ('tag', 'testproduct-1.0-build'),
            ('tag', 'testproduct-1.0-candidate'),
            ('tag', 'testproduct-1.0-released'),
            ('tag', 'testproduct-1.0'),
            ('target', 'testproduct-1.0-candidate'),
            ('target', 'testproduct-1.0-release'),
            ('tag', 'testproduct-2.0-build'),
            ('tag', 'testproduct-2.0-candidate'),
            ('tag', 'testproduct-2.0-released'),
            ('tag', 'testproduct-2.0'),
            ('target', 'testproduct-2.0-candidate'),
            ('target', 'testproduct-2.0-release'),
            # Implicit missing permissions
            ('permission', 'testproduct-pkglist'),
            ('permission', 'testproduct-taggers')
        ]
        assert_contains_objects(self, resolved_objects, expected_keys)

        # Should have resolved all objects without getting stuck
        self.assertEqual(len(resolved_objects), 15)

        # Should have no remaining items
        self.assertEqual(len(solver.remaining_keys()), 0)

    def test_template_based_dependencies_partial_work(self):
        """Test solver with partial work list on template-generated dependencies."""
        # Only include some targets in work list
        work_keys = [
            ('target', 'testproduct-1.0-candidate'),
            ('target', 'testproduct-2.0-release')
        ]
        solver = create_solver_with_files(['product_template.yaml', 'testproduct.yaml'], work_keys=work_keys)
        solver.prepare()

        # Resolve objects
        resolved_objects = list(solver)

        # Should resolve the requested targets and all their dependencies
        expected_keys = [
            # Requested targets
            ('target', 'testproduct-1.0-candidate'),
            ('target', 'testproduct-2.0-release'),
            # Dependencies for testproduct-1.0-candidate
            ('tag', 'testproduct-1.0-build'),
            ('tag', 'testproduct-1.0-candidate'),
            ('tag', 'testproduct-1.0'),
            ('tag', 'testproduct-1.0-released'),
            # Dependencies for testproduct-2.0-release
            ('tag', 'testproduct-2.0-candidate'),
            ('tag', 'testproduct-2.0-released'),
            ('tag', 'testproduct-2.0'),

        ]
        assert_contains_objects(self, resolved_objects, expected_keys)

        # Should not resolve objects not needed for the work items
        resolved_keys = [obj.key() for obj in resolved_objects]
        self.assertNotIn(('group', 'testproduct-packagers'), resolved_keys)
        self.assertNotIn(('permission', 'testproduct-pkglist'), resolved_keys)
        self.assertNotIn(('permission', 'testproduct-taggers'), resolved_keys)
        self.assertNotIn(('tag', 'testproduct-2.0-build'), resolved_keys)
        self.assertNotIn(('target', 'testproduct-1.0-release'), resolved_keys)
        self.assertNotIn(('target', 'testproduct-2.0-candidate'), resolved_keys)

    def test_template_based_dependencies_ordering(self):
        """Test that template-generated dependencies are resolved in correct order."""
        solver = create_solver_with_files(['product_template.yaml', 'testproduct.yaml'])
        solver.prepare()

        # Resolve objects
        resolved_objects = list(solver)
        resolved_keys = [obj.key() for obj in resolved_objects]

        # Base tags should be resolved before build tags
        base_tag_pos = resolved_keys.index(('tag', 'testproduct-1.0'))
        build_tag_pos = resolved_keys.index(('tag', 'testproduct-1.0-build'))
        self.assertLess(base_tag_pos, build_tag_pos,
                       "Base tag should be resolved before build tag")

        # Build tags should be resolved before targets
        build_tag_pos = resolved_keys.index(('tag', 'testproduct-1.0-build'))
        target_pos = resolved_keys.index(('target', 'testproduct-1.0-candidate'))
        self.assertLess(build_tag_pos, target_pos,
                       "Build tag should be resolved before target")

        # Candidate tags should be resolved before targets that use them
        candidate_tag_pos = resolved_keys.index(('tag', 'testproduct-1.0-candidate'))
        target_pos = resolved_keys.index(('target', 'testproduct-1.0-candidate'))
        self.assertLess(candidate_tag_pos, target_pos,
                       "Candidate tag should be resolved before target")

    def test_template_based_dependencies_with_missing_dependencies(self):
        """Test template-generated dependencies mixed with missing dependencies."""
        # Use multiple files to create a complex scenario
        solver = create_solver_with_files([
            'product_template.yaml',
            'testproduct.yaml',
            'missing_dependencies.yaml'
        ])
        solver.prepare()

        # Resolve objects
        resolved_objects = list(solver)

        # Should contain objects from all files
        expected_keys = [
            # From product template and testproduct
            ('group', 'testproduct-packagers'),
            ('tag', 'testproduct-1.0-build'),
            ('tag', 'testproduct-1.0-candidate'),
            ('tag', 'testproduct-1.0-released'),
            ('tag', 'testproduct-1.0'),
            ('target', 'testproduct-1.0-candidate'),
            ('target', 'testproduct-1.0-release'),
            ('tag', 'testproduct-2.0-build'),
            ('tag', 'testproduct-2.0-candidate'),
            ('tag', 'testproduct-2.0-released'),
            ('tag', 'testproduct-2.0'),
            ('target', 'testproduct-2.0-candidate'),
            ('target', 'testproduct-2.0-release'),
            # From missing_dependencies.yaml
            ('tag', 'child-tag'),
            ('target', 'missing-target'),
            ('user', 'user-with-missing-group'),
            ('tag', 'tag-with-missing-repo'),
            # Missing dependencies
            ('tag', 'missing-parent-tag'),
            ('tag', 'missing-build-tag'),
            ('tag', 'missing-dest-tag'),
            ('group', 'missing-group'),
            ('permission', 'missing-permission'),
            ('external-repo', 'missing-external-repo'),
            # Implicit missing permissions
            ('permission', 'testproduct-pkglist'),
            ('permission', 'testproduct-taggers')
        ]
        assert_contains_objects(self, resolved_objects, expected_keys)

        # Should have resolved all objects
        self.assertEqual(len(resolved_objects), 25)

    def test_template_based_dependencies_reporting(self):
        """Test that template-generated dependencies don't affect missing dependency reporting."""
        solver = create_solver_with_files(['product_template.yaml', 'testproduct.yaml'])
        solver.prepare()

        # Should only have the 2 implicit missing permissions
        report = solver.report()
        self.assertEqual(len(report.phantoms), 2)

        # After resolving, should still have the 2 implicit missing permissions
        resolved_objects = list(solver)
        report_after = solver.report()
        self.assertEqual(len(report_after.phantoms), 2)

    def test_template_based_dependencies_complex_workflow(self):
        """Test complex workflow with template-generated dependencies."""
        # Test a realistic scenario where we only want to build specific targets
        work_keys = [
            ('target', 'testproduct-1.0-candidate'),
            ('target', 'testproduct-2.0-release')
        ]
        solver = create_solver_with_files(['product_template.yaml', 'testproduct.yaml'], work_keys=work_keys)
        solver.prepare()

        # Resolve objects
        resolved_objects = list(solver)
        resolved_keys = [obj.key() for obj in resolved_objects]

        # Should have resolved the requested targets
        self.assertIn(('target', 'testproduct-1.0-candidate'), resolved_keys)
        self.assertIn(('target', 'testproduct-2.0-release'), resolved_keys)

        # Should have resolved their dependencies
        self.assertIn(('tag', 'testproduct-1.0-build'), resolved_keys)
        self.assertIn(('tag', 'testproduct-1.0-candidate'), resolved_keys)
        self.assertIn(('tag', 'testproduct-2.0-candidate'), resolved_keys)
        self.assertIn(('tag', 'testproduct-2.0-released'), resolved_keys)

        # Should not have resolved unnecessary objects
        self.assertNotIn(('target', 'testproduct-1.0-release'), resolved_keys)
        self.assertNotIn(('target', 'testproduct-2.0-candidate'), resolved_keys)


class TestSolverIntegration(unittest.TestCase):
    """
    Integration tests for Resolver + Solver working together.

    These tests combine multiple files and complex scenarios to validate
    the complete dependency resolution workflow.
    """

    def test_complete_workflow_simple_chain(self):
        """Test complete workflow with simple dependency chain."""
        solver = create_solver_with_files(['simple_chain.yaml'])
        solver.prepare()

        # Resolve all objects
        resolved_objects = list(solver)

        # Should resolve in correct order: tag3 -> tag2 -> tag1
        expected_order = [
            ('tag', 'tag3'),
            ('tag', 'tag2'),
            ('tag', 'tag1')
        ]
        assert_dependency_order(self, resolved_objects, expected_order)

        # Should have no remaining items
        self.assertEqual(len(solver.remaining_keys()), 0)

        # Should have no missing dependencies
        report = solver.report()
        self.assertEqual(len(report.phantoms), 0)

    def test_complete_workflow_mixed_dependencies(self):
        """Test complete workflow with mixed dependency types."""
        solver = create_solver_with_files([
            'independent_objects.yaml',
            'target_dependencies.yaml',
            'user_group_dependencies.yaml'
        ], redefine=Redefine.IGNORE)
        solver.prepare()

        # Resolve all objects
        resolved_objects = list(solver)
        resolved_keys = [obj.key() for obj in resolved_objects]

        # Should contain objects from all files
        # Note: admin permission is defined in both files, causing a namespace conflict
        expected_keys = [
            # From independent_objects.yaml
            ('user', 'build-user'),
            ('user', 'release-user'),
            ('permission', 'admin'),  # Will be from user_group_dependencies.yaml due to conflict
            ('external-repo', 'epel-9'),
            # From target_dependencies.yaml
            ('tag', 'build-tag'),
            ('tag', 'dest-tag'),
            ('target', 'myproject-build'),
            ('target', 'myproject-release'),
            # From user_group_dependencies.yaml
            ('group', 'packagers'),
            ('group', 'release-team'),
            ('user', 'packager1'),
            ('user', 'packager2'),
            ('user', 'release-manager'),
            # Missing permissions referenced by groups but not defined
            ('permission', 'pkglist'),
            ('permission', 'taggers'),
            ('permission', 'release'),
            ('permission', 'sign')
        ]
        assert_contains_objects(self, resolved_objects, expected_keys)

        # there's two ignored duplicates
        self.assertEqual(len(resolved_objects), 17)

        # Should have no remaining items
        self.assertEqual(len(solver.remaining_keys()), 0)

    def test_complete_workflow_with_missing_dependencies(self):
        """Test complete workflow with missing dependencies."""
        solver = create_solver_with_files(['missing_dependencies.yaml'])
        solver.prepare()

        # Should have missing dependencies before resolution
        report_before = solver.report()
        self.assertEqual(len(report_before.phantoms), 6)
        self.assertIn(('tag', 'missing-parent-tag'), report_before.phantoms)
        self.assertIn(('tag', 'missing-build-tag'), report_before.phantoms)
        self.assertIn(('tag', 'missing-dest-tag'), report_before.phantoms)
        self.assertIn(('group', 'missing-group'), report_before.phantoms)
        self.assertIn(('permission', 'missing-permission'), report_before.phantoms)
        self.assertIn(('external-repo', 'missing-external-repo'), report_before.phantoms)

        # Resolve all objects
        resolved_objects = list(solver)

        # Should contain the objects that could be resolved
        expected_keys = [
            # From missing_dependencies.yaml
            ('tag', 'child-tag'),
            ('target', 'missing-target'),
            ('user', 'user-with-missing-group'),
            ('tag', 'tag-with-missing-repo'),
            # all the implicit missing items
            ('tag', 'missing-parent-tag'),
            ('tag', 'missing-build-tag'),
            ('tag', 'missing-dest-tag'),
            ('group', 'missing-group'),
            ('permission', 'missing-permission'),
            ('external-repo', 'missing-external-repo'),
        ]
        assert_contains_objects(self, resolved_objects, expected_keys)

        # Should have resolved 3 objects
        self.assertEqual(len(resolved_objects), 10)

        # Should have no remaining items (missing objects are handled gracefully)
        self.assertEqual(len(solver.remaining_keys()), 0)

        # Should still have missing dependencies after resolution
        report_after = solver.report()
        self.assertEqual(len(report_after.phantoms), 6)

    def test_complete_workflow_circular_dependencies(self):
        """Test complete workflow with circular dependencies."""
        solver = create_solver_with_files(['circular_dependencies.yaml'])
        solver.prepare()

        # Resolve all objects
        resolved_objects = list(solver)
        resolved_keys = [obj.key() for obj in resolved_objects]
        print(resolved_keys)

        # Should contain all objects from the circular dependency
        expected_keys = [
            ('tag-split', 'tag-a'),
            ('tag', 'tag-a'),
            ('tag', 'tag-b'),
            ('tag', 'tag-c')
        ]
        assert_contains_objects(self, resolved_objects, expected_keys)

        self.assertEqual(len(resolved_objects), 4)

        # Should have no remaining items
        self.assertEqual(len(solver.remaining_keys()), 0)

        # Should have no missing dependencies
        report = solver.report()
        self.assertEqual(len(report.phantoms), 0)

    def test_partial_workflow_complex_scenario(self):
        """Test partial workflow with specific work items from complex scenario."""
        work_keys = [
            ('target', 'myproject-build'),
            ('target', 'testproduct-1.0-candidate')
        ]
        solver = create_solver_with_files([
            'cross_dependencies.yaml',
            'product_template.yaml',
            'testproduct.yaml'
        ], work_keys=work_keys)
        solver.prepare()

        # Resolve objects
        resolved_objects = list(solver)
        resolved_keys = [obj.key() for obj in resolved_objects]

        # Should have resolved the requested targets and their dependencies
        expected_keys = [
            # Dependencies for myproject-target
            ('tag', 'build-tag'),
            ('tag', 'base-tag'),
            ('target', 'myproject-build'),
            # Dependencies for testproduct-1.0-candidate
            ('tag', 'testproduct-1.0'),
            ('tag', 'testproduct-1.0-released'),
            ('tag', 'testproduct-1.0-build'),
            ('tag', 'testproduct-1.0-candidate'),
            ('target', 'testproduct-1.0-candidate')
        ]
        assert_contains_objects(self, resolved_objects, expected_keys)

        # Should not have resolved unnecessary objects
        self.assertNotIn(('user', 'myproject-user'), resolved_keys)
        self.assertNotIn(('group', 'myproject-group'), resolved_keys)
        self.assertNotIn(('permission', 'myproject-perm'), resolved_keys)
        self.assertNotIn(('external-repo', 'myproject-repo'), resolved_keys)
        self.assertNotIn(('tag', 'testproduct-2.0'), resolved_keys)
        self.assertNotIn(('target', 'testproduct-2.0-candidate'), resolved_keys)

    def test_workflow_with_mixed_missing_and_circular(self):
        """Test workflow combining missing dependencies and circular dependencies."""
        solver = create_solver_with_files([
            'missing_dependencies.yaml',
            'circular_dependencies.yaml'
        ])
        solver.prepare()

        # Should have missing dependencies before resolution
        report_before = solver.report()
        self.assertEqual(len(report_before.phantoms), 6)

        # Resolve all objects
        resolved_objects = list(solver)
        resolved_keys = [obj.key() for obj in resolved_objects]

        # Should contain objects from both files
        expected_keys = [
            # From missing_dependencies.yaml
            ('tag', 'child-tag'),
            ('target', 'missing-target'),
            ('user', 'user-with-missing-group'),
            ('tag', 'tag-with-missing-repo'),
            # From circular_dependencies.yaml
            ('tag-split', 'tag-a'),
            ('tag', 'tag-a'),
            ('tag', 'tag-b'),
            ('tag', 'tag-c'),
            # all the implicit missing items
            ('tag', 'missing-parent-tag'),
            ('tag', 'missing-build-tag'),
            ('tag', 'missing-dest-tag'),
            ('group', 'missing-group'),
            ('permission', 'missing-permission'),
            ('external-repo', 'missing-external-repo'),
        ]
        assert_contains_objects(self, resolved_objects, expected_keys)

        # 4 objects from missing_dependencies.yaml
        #  + 6 implicit missing items
        #  + 3 from circular_dependencies.yaml
        #  + 1 split object from circular_dependencies.yaml
        self.assertEqual(len(resolved_objects), 14)

        # Should have no remaining items
        self.assertEqual(len(solver.remaining_keys()), 0)

        # Should still have missing dependencies after resolution
        report_after = solver.report()
        self.assertEqual(len(report_after.phantoms), 6)

    def test_workflow_error_handling(self):
        """Test workflow error handling and edge cases."""
        # Test with empty work list
        solver = create_solver_with_files(['simple_chain.yaml'], work_keys=[])
        solver.prepare()

        resolved_objects = list(solver)
        self.assertEqual(len(resolved_objects), 0)
        self.assertEqual(len(solver.remaining_keys()), 0)

        # Test with non-existent work items
        solver = create_solver_with_files(['simple_chain.yaml'], work_keys=[('tag', 'nonexistent')])
        solver.prepare()

        resolved_objects = list(solver)
        self.assertEqual(len(resolved_objects), 1)
        self.assertEqual(len(solver.remaining_keys()), 0)

        # Should have missing dependency
        report = solver.report()
        self.assertEqual(len(report.phantoms), 1)
        self.assertIn(('tag', 'nonexistent'), report.phantoms)

    def test_workflow_consistency_across_runs(self):
        """Test that workflow produces consistent results across multiple runs."""
        # Run the same scenario multiple times
        results = []
        for _ in range(3):
            solver = create_solver_with_files(['cross_dependencies.yaml'])
            solver.prepare()
            resolved_objects = list(solver)
            resolved_keys = [obj.key() for obj in resolved_objects]
            results.append(resolved_keys)

        # All runs should produce the same results
        for i in range(1, len(results)):
            self.assertEqual(results[0], results[i],
                           f"Run {i} produced different results than run 0")

    def test_workflow_reporting_consistency(self):
        """Test that reporting is consistent before and after resolution."""
        solver = create_solver_with_files(['missing_dependencies.yaml'])
        solver.prepare()

        # Get report before resolution
        report_before = solver.report()
        missing_before = set(report_before.phantoms)

        # Resolve objects
        resolved_objects = list(solver)

        # Get report after resolution
        report_after = solver.report()
        missing_after = set(report_after.phantoms)

        # Missing dependencies should be the same
        self.assertEqual(missing_before, missing_after,
                        "Missing dependencies should not change after resolution")

        # Should have resolved some objects
        self.assertGreater(len(resolved_objects), 0)


# The end.

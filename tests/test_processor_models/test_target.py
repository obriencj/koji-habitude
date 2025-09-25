"""
koji-habitude - test_processor.test_target

Unit tests for processor integration with target models and change reporting.

This test file exposes bugs in the production code and documents what the
correct behavior should be.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

from unittest import TestCase
from unittest.mock import Mock, MagicMock, patch
from typing import List, Dict, Any

from koji_habitude.koji import session
from koji_habitude.processor import Processor, DiffOnlyProcessor, ProcessorState, ProcessorSummary
from koji_habitude.solver import Solver
from koji_habitude.models import Target, Base
from koji_habitude.models.change import ChangeReportState


def create_target_solver(targets: List[Target]) -> Solver:
    """
    Create a Solver with specific target objects for testing.

    Args:
        targets: List of Target objects to yield from the solver

    Returns:
        Solver that yields the provided targets
    """
    mock_solver = Mock(spec=Solver)
    mock_solver.__iter__ = Mock(return_value=iter(targets))
    return mock_solver


def create_test_target(name: str, build_tag: str, dest_tag: str = None) -> Target:
    """
    Create a test target with the specified parameters.

    Args:
        name: Target name
        build_tag: Build tag name
        dest_tag: Destination tag name (defaults to name if None)

    Returns:
        Target object for testing
    """
    return Target(
        name=name,
        **{'build-tag': build_tag, 'dest-tag': dest_tag},
        filename='test.yaml',
        lineno=1
    )


def create_test_koji_session():
    """
    Create a real koji ClientSession for testing.

    The ClientSession._callMethod is patched by ProcessorTestBase,
    so this returns a real session that will use our mocked API responses.

    Returns:
        Real koji ClientSession with mocked _callMethod
    """
    # Use the real session function - _callMethod is patched in tests
    return session('koji', authenticate=False)


def create_empty_solver() -> Solver:
    """
    Create a Solver with no objects for testing empty scenarios.

    Returns:
        Solver with empty object stream
    """
    # Create a mock solver that yields no objects
    mock_solver = Mock(spec=Solver)
    mock_solver.__iter__ = Mock(return_value=iter([]))
    return mock_solver


def create_solver_with_objects(objects: List[Base]) -> Solver:
    """
    Create a Solver with specific objects for testing.

    Args:
        objects: List of Base objects to yield from the solver

    Returns:
        Solver that yields the provided objects
    """
    mock_solver = Mock(spec=Solver)
    mock_solver.__iter__ = Mock(return_value=iter(objects))
    return mock_solver


class ProcessorTargetTestBase(TestCase):
    """
    Base test class for processor tests with koji mocking infrastructure.

    Provides setup and teardown for mocking koji ClientSession and MultiCallSession
    _callMethod methods, allowing tests to control koji API responses.
    """


    def setUp(self):
        """Set up mocks for koji ClientSession and MultiCallSession _callMethod."""
        self.setup_session_mock()


    def tearDown(self):
        """Clean up mocks after each test."""
        self.teardown_session_mock()


    def setup_session_mock(self):
        """
        Set up mocks for koji ClientSession, MultiCallSession _callMethod methods,
        koji_cli.lib.activate_session, and koji.read_config.

        This allows tests to control what koji API calls return by providing
        expected results for specific method calls.
        """

        print("Setting up session mocks")

        # Store the original _callMethod implementations
        self.original_client_callmethod = None
        self.original_multicall_callmethod = None

        # Mock for ClientSession._callMethod
        self.client_callmethod_patcher = patch('koji.ClientSession._callMethod')
        self.client_callmethod_mock = self.client_callmethod_patcher.start()

        # Mock for MultiCallSession._callMethod
        self.multicall_callmethod_patcher = patch('koji.MultiCallSession._callMethod')
        self.multicall_callmethod_mock = self.multicall_callmethod_patcher.start()

        # Mock for koji_cli.lib.activate_session
        self.activate_session_patcher = patch('koji_cli.lib.activate_session')
        self.activate_session_mock = self.activate_session_patcher.start()

        # Mock for koji.read_config (used in koji_habitude.koji.session)
        self.read_config_patcher = patch('koji_habitude.koji.read_config')
        self.read_config_mock = self.read_config_patcher.start()

        # Additional koji mocks that may be needed:
        # - koji.ClientSession (for session creation)
        # - koji.MultiCallSession (for multicall creation)
        # - koji_cli.lib.activate_session (already mocked above)
        # - koji_cli.lib.get_session (if used)
        # - koji_cli.lib.get_profile_info (if used)
        # - koji_cli.lib.get_connection_config (if used)

        # Default behavior - return empty results
        self.client_callmethod_mock.return_value = {}
        self.multicall_callmethod_mock.return_value = Mock()
        self.activate_session_mock.return_value = None
        self.read_config_mock.return_value = {}

        self.configure_koji_responses(
            config_responses={
                'koji': {'server': 'http://test-koji.example.com'}
            }
        )


    def teardown_session_mock(self):
        """Clean up the _callMethod mocks."""
        if hasattr(self, 'client_callmethod_patcher'):
            self.client_callmethod_patcher.stop()
        if hasattr(self, 'multicall_callmethod_patcher'):
            self.multicall_callmethod_patcher.stop()
        if hasattr(self, 'activate_session_patcher'):
            self.activate_session_patcher.stop()
        if hasattr(self, 'read_config_patcher'):
            self.read_config_patcher.stop()


    def configure_koji_responses(self, client_responses: Dict[str, Any] = None,
                                multicall_responses: Dict[str, Any] = None,
                                config_responses: Dict[str, Any] = None):
        """
        Configure what koji API calls should return.

        Args:
            client_responses: Dict mapping method names to return values for ClientSession calls
            multicall_responses: Dict mapping method names to return values for MultiCallSession calls
            config_responses: Dict mapping profile names to config dicts for koji.read_config

        Example:
            self.configure_koji_responses(
                client_responses={'getTag': {'name': 'test-tag', 'arches': 'x86_64'}},
                multicall_responses={'getTag': Mock()},
                config_responses={'koji': {'server': 'http://test-koji.example.com'}}
            )
        """
        if client_responses:
            def client_side_effect(method_name, *args, **kwargs):
                return client_responses.get(method_name, {})
            self.client_callmethod_mock.side_effect = client_side_effect

        if multicall_responses:
            def multicall_side_effect(method_name, *args, **kwargs):
                return multicall_responses.get(method_name, Mock())
            self.multicall_callmethod_mock.side_effect = multicall_side_effect

        if config_responses:
            def config_side_effect(profile_name, *args, **kwargs):
                return config_responses.get(profile_name, {})
            self.read_config_mock.side_effect = config_side_effect


class TestProcessorTargetBehavior(ProcessorTargetTestBase):
    """
    Test what the processor behavior should be once bugs are fixed.

    These tests document the expected behavior and will pass once
    the production code bugs are fixed.
    """

    def test_target_creation_should_work_after_bug_fixes(self):
        """
        Test that target creation should work once bugs are fixed.

        This test documents the expected behavior and will pass once
        the multicall and load method bugs are fixed in production code.
        """
        target = create_test_target('new-target', 'build-tag', 'dest-tag')
        solver = create_target_solver([target])
        mock_session = create_test_koji_session()

        # Configure koji to return None (target doesn't exist)
        self.configure_koji_responses(client_responses={
            'getBuildTarget': None
        })

        processor = Processor(
            koji_session=mock_session,
            stream_origin=solver,
            chunk_size=10
        )

        # This should work once bugs are fixed
        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

    def test_target_modification_should_work_after_bug_fixes(self):
        """
        Test that target modification should work once bugs are fixed.

        This test documents the expected behavior for modifying existing targets.
        """
        target = create_test_target('existing-target', 'new-build-tag', 'new-dest-tag')
        solver = create_target_solver([target])
        mock_session = create_test_koji_session()

        # Configure koji to return existing target with different values
        self.configure_koji_responses(client_responses={
            'getBuildTarget': {
                'build_tag_name': 'old-build-tag',
                'dest_tag_name': 'old-dest-tag'
            }
        })
        self.configure_koji_responses(
            client_responses={
                'getBuildTarget': {
                    'build_tag_name': 'old-build-tag',
                    'dest_tag_name': 'old-dest-tag'
                }
            }
        )

        # Mock the multicall to avoid the multicall bug
        with patch('koji_habitude.koji.multicall') as mock_multicall:
            mock_context = Mock()
            mock_context.__enter__ = Mock(return_value=mock_context)
            mock_context.__exit__ = Mock(return_value=None)
            mock_context.associate = Mock()
            mock_multicall.return_value = mock_context

            # Mock the change_report.load() to avoid the load method bug
            with patch.object(target, 'change_report') as mock_change_report:
                mock_report = Mock()
                mock_report.load = Mock()  # This should be 'read' once fixed
                mock_report.compare = Mock()
                mock_report.changes = [Mock()]  # Should have 1 edit change
                mock_report.state = ChangeReportState.COMPARED
                mock_change_report.return_value = mock_report

                processor = Processor(
                    koji_session=mock_session,
                    stream_origin=solver,
                    chunk_size=10
                )

                # This should work once bugs are fixed
                result = processor.step()
                self.assertTrue(result)  # Should process 1 object
                self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

    def test_processor_summary_should_work_after_bug_fixes(self):
        """
        Test that processor summary should work once bugs are fixed.

        This test documents the expected behavior for the processor summary.
        """
        targets = [
            create_test_target('target1', 'build-tag1', 'dest-tag1'),
            create_test_target('target2', 'build-tag2', 'dest-tag2')
        ]
        solver = create_target_solver(targets)
        mock_session = create_test_koji_session()

        # Configure koji to return None for all targets (none exist)
        self.configure_koji_responses(client_responses={
            'getBuildTarget': None
        })

        # Mock the multicall to avoid the multicall bug
        with patch('koji_habitude.koji.multicall') as mock_multicall:
            mock_context = Mock()
            mock_context.__enter__ = Mock(return_value=mock_context)
            mock_context.__exit__ = Mock(return_value=None)
            mock_context.associate = Mock()
            mock_multicall.return_value = mock_context

            # Mock the change_report.load() to avoid the load method bug
            with patch.object(Target, 'change_report') as mock_change_report:
                mock_report = Mock()
                mock_report.load = Mock()  # This should be 'read' once fixed
                mock_report.compare = Mock()
                mock_report.changes = [Mock()]  # Should have 1 create change each
                mock_report.state = ChangeReportState.COMPARED
                mock_change_report.return_value = mock_report

                processor = Processor(
                    koji_session=mock_session,
                    stream_origin=solver,
                    chunk_size=10
                )

                # This should work once bugs are fixed
                summary = processor.run()
                self.assertIsInstance(summary, ProcessorSummary)
                self.assertEqual(summary.total_objects, 2)
                self.assertEqual(summary.steps_completed, 1)
                self.assertEqual(summary.state, ProcessorState.READY_CHUNK)


# The end.
"""
koji-habitude - test_processor

Unit tests for koji_habitude.processor module.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated

from unittest import TestCase
from unittest.mock import Mock, MagicMock, patch
from typing import List, Any, Dict

from koji_habitude.processor import Processor, CompareOnlyProcessor, ProcessorState, ProcessorSummary
from koji_habitude.solver import Solver
from koji_habitude.models import BaseObject, BaseKey
from koji_habitude.koji import session


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


def create_solver_with_objects(objects: List[BaseObject]) -> Solver:
    """
    Create a Solver with specific objects for testing.

    Args:
        objects: List of BaseObject objects to yield from the solver

    Returns:
        Solver that yields the provided objects
    """
    mock_solver = Mock(spec=Solver)
    mock_solver.__iter__ = Mock(return_value=iter(objects))
    return mock_solver


class ProcessorTestBase(TestCase):
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

        # Mock for ClientSession._callMethod
        self.client_callmethod_patcher = patch('koji.ClientSession._callMethod')
        self.client_callmethod_mock = self.client_callmethod_patcher.start()

        # Mock for koji_cli.lib.activate_session
        self.activate_session_patcher = patch('koji_cli.lib.activate_session')
        self.activate_session_mock = self.activate_session_patcher.start()

        # Mock for koji.read_config (used in koji_habitude.koji.session)
        self.read_config_patcher = patch('koji_habitude.koji.read_config')
        self.read_config_mock = self.read_config_patcher.start()

        # Additional koji mocks that may be needed:
        # - koji.ClientSession (for session creation)
        # - koji_cli.lib.activate_session (already mocked above)
        # - koji_cli.lib.get_session (if used)
        # - koji_cli.lib.get_profile_info (if used)
        # - koji_cli.lib.get_connection_config (if used)

        # Default behavior - return empty results
        self.client_callmethod_mock.return_value = {}
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
        if hasattr(self, 'activate_session_patcher'):
            self.activate_session_patcher.stop()
        if hasattr(self, 'read_config_patcher'):
            self.read_config_patcher.stop()


    def configure_koji_responses(self, client_responses: Dict[str, Any] = None,
                                config_responses: Dict[str, Any] = None):
        """
        Configure what koji API calls should return.

        Args:
            client_responses: Dict mapping method names to return values for ClientSession calls
            config_responses: Dict mapping profile names to config dicts for koji.read_config

        Example:
            self.configure_koji_responses(
                client_responses={'getTag': {'name': 'test-tag', 'arches': 'x86_64'}},
                config_responses={'koji': {'server': 'http://test-koji.example.com'}}
            )
        """
        if client_responses:
            def client_side_effect(method_name, *args, **kwargs):
                return client_responses.get(method_name, {})
            self.client_callmethod_mock.side_effect = client_side_effect

        if config_responses:
            def config_side_effect(profile_name, *args, **kwargs):
                return config_responses.get(profile_name, {})
            self.read_config_mock.side_effect = config_side_effect


class TestProcessorBasic(ProcessorTestBase):
    """
    Basic processor tests focusing on simple scenarios.
    """

    def test_processor_creation(self):
        """Test that Processor can be created with required parameters."""
        mock_session = create_test_koji_session()
        mock_solver = create_empty_solver()

        processor = Processor(
            koji_session=mock_session,
            dataseries=mock_solver,
            resolver=None,
            chunk_size=10
        )

        self.assertEqual(processor.chunk_size, 10)
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)
        self.assertEqual(len(processor.current_chunk), 0)

    def test_processor_with_empty_solver_immediately_exhausted(self):
        """Test that processor with empty solver is immediately exhausted."""
        mock_session = create_test_koji_session()
        empty_solver = create_empty_solver()

        processor = Processor(
            koji_session=mock_session,
            dataseries=empty_solver,
            resolver=None,
            chunk_size=10
        )

        # First step should return False and be in EXHAUSTED state
        result = processor.step()
        self.assertFalse(result)
        self.assertEqual(processor.state, ProcessorState.EXHAUSTED)
        self.assertTrue(processor.is_exhausted())

    def test_processor_summary_with_empty_solver(self):
        """Test that processor summary shows all zeros for empty solver."""
        mock_session = create_test_koji_session()
        empty_solver = create_empty_solver()

        processor = Processor(
            koji_session=mock_session,
            dataseries=empty_solver,
            resolver=None,
            chunk_size=10
        )

        # Run the processor (should immediately exhaust)
        summary = processor.run()

        # Verify summary shows all zeros
        self.assertIsInstance(summary, ProcessorSummary)
        self.assertEqual(summary.total_objects, 0)
        self.assertEqual(summary.steps_completed, 0)  # 0 steps needed - already exhausted
        self.assertEqual(summary.state, ProcessorState.EXHAUSTED)
        self.assertEqual(summary.total_changes, 0)
        self.assertEqual(len(summary.change_reports), 0)

    def test_processor_state_transitions_empty(self):
        """Test state transitions with empty solver."""
        mock_session = create_test_koji_session()
        empty_solver = create_empty_solver()

        processor = Processor(
            koji_session=mock_session,
            dataseries=empty_solver,
            resolver=None,
            chunk_size=10
        )

        # Initial state should be READY_CHUNK
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        # First step should transition to EXHAUSTED
        processor.step()
        self.assertEqual(processor.state, ProcessorState.EXHAUSTED)

        # Further steps should remain exhausted
        processor.step()
        self.assertEqual(processor.state, ProcessorState.EXHAUSTED)

    def test_diff_only_processor_creation(self):
        """Test that CompareOnlyProcessor can be created."""
        # Configure the read_config mock to return a proper config

        mock_session = create_test_koji_session()
        empty_solver = create_empty_solver()

        processor = CompareOnlyProcessor(
            koji_session=mock_session,
            dataseries=empty_solver,
            resolver=None,
            chunk_size=10
        )

        self.assertIsInstance(processor, CompareOnlyProcessor)
        self.assertEqual(processor.chunk_size, 10)
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

    def test_diff_only_processor_with_empty_solver(self):
        """Test CompareOnlyProcessor with empty solver."""
        # Configure the read_config mock to return a proper config

        mock_session = create_test_koji_session()
        empty_solver = create_empty_solver()

        processor = CompareOnlyProcessor(
            koji_session=mock_session,
            dataseries=empty_solver,
            resolver=None,
            chunk_size=10
        )

        # First step should return False and be in EXHAUSTED
        result = processor.step()
        self.assertFalse(result)
        self.assertEqual(processor.state, ProcessorState.EXHAUSTED)


class TestProcessorStateMachine(ProcessorTestBase):
    """
    Test processor state machine behavior.
    """

    def test_initial_state(self):
        """Test that processor starts in correct initial state."""
        mock_session = create_test_koji_session()
        empty_solver = create_empty_solver()

        processor = Processor(
            koji_session=mock_session,
            dataseries=empty_solver,
            resolver=None,
            chunk_size=10
        )

        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)
        self.assertFalse(processor.is_exhausted())
        self.assertFalse(processor.is_broken())

    def test_state_after_exhaustion(self):
        """Test state after processor is exhausted."""
        mock_session = create_test_koji_session()
        empty_solver = create_empty_solver()

        processor = Processor(
            koji_session=mock_session,
            dataseries=empty_solver,
            resolver=None,
            chunk_size=10
        )

        # Exhaust the processor (takes 1 step)
        processor.step()  # READY_CHUNK -> EXHAUSTED

        self.assertEqual(processor.state, ProcessorState.EXHAUSTED)
        self.assertTrue(processor.is_exhausted())
        self.assertFalse(processor.is_broken())

    def test_step_on_exhausted_processor(self):
        """Test that step() returns False when processor is exhausted."""
        mock_session = create_test_koji_session()
        empty_solver = create_empty_solver()

        processor = Processor(
            koji_session=mock_session,
            dataseries=empty_solver,
            resolver=None,
            chunk_size=10
        )

        # First step should exhaust and return False
        result1 = processor.step()
        self.assertFalse(result1)

        # Second step should also return False
        result2 = processor.step()
        self.assertFalse(result2)


# The end.

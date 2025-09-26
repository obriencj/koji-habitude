""""
Shared test infrastructure for processor models.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated with Human Rework


from unittest.mock import patch
from typing import List, Tuple, Any, Dict

from koji import ClientSession
from unittest.mock import Mock, patch

from koji_habitude.koji import session
from koji_habitude.solver import Solver
from koji_habitude.models import Base


def create_test_koji_session():
    """
    Create a real koji ClientSession for testing.

    The ClientSession._callMethod is patched by ProcessorTestBase,
    so this returns a real session that will use our mocked API responses.

    Returns:
        Real koji ClientSession with mocked _callMethod
    """

    sess = session('koji', authenticate=False)
    vars(sess)['_currentuser'] = {'id': 1234, 'name': 'testuser'}
    return sess


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


class MulticallMocking:
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
        Set up mocks for koji ClientSession._callMethod,
        koji_cli.lib.activate_session, and koji.read_config.

        This allows tests to control what koji API calls return by providing
        expected results for specific method calls.
        """

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
        # - koji.MultiCallSession (for multicall creation)
        # - koji_cli.lib.activate_session (already mocked above)
        # - koji_cli.lib.get_session (if used)
        # - koji_cli.lib.get_profile_info (if used)
        # - koji_cli.lib.get_connection_config (if used)

        # Default behavior - return empty results
        self.activate_session_mock.return_value = None
        self.read_config_mock.return_value = {}

        self.client_responses = {}

        self.configure_koji_responses(
            config_responses={
                'koji': {'server': 'http://test-koji.example.com'}
            }
        )

        def client_side_effect(method_name, *args, **kwargs):
            # Handle the actual multicall execution
            if method_name == 'multiCall':
                # The multicall format is multiCall((calls,), {}) where calls is a list of call objects
                calls = args[0][0] if args and args[0] else []
                results = []

                # Process each call in the multicall batch
                for call in calls:
                    call_method = call.get('methodName', '')
                    call_params = call.get('params', ())
                    results.append([client_side_effect(call_method, *call_params)])

                return results

            else:
                resp = self.client_responses.get(method_name, []).pop(0)
                if callable(resp):
                    if args and isinstance(args[-1], dict) and "__starstar" in args[-1]:
                        kwargs = args[-1]
                        kwargs.pop("__starstar")
                        args = args[:-1]
                    return resp(*args, **kwargs)
                return resp


        self.client_callmethod_mock.side_effect = client_side_effect


    def teardown_session_mock(self):
        """Clean up the _callMethod mocks."""
        if hasattr(self, 'client_callmethod_patcher'):
            self.client_callmethod_patcher.stop()
        if hasattr(self, 'activate_session_patcher'):
            self.activate_session_patcher.stop()
        if hasattr(self, 'read_config_patcher'):
            self.read_config_patcher.stop()


    def configure_koji_responses(
        self,
        client_responses: List[Tuple[str, Any]] = (),
        config_responses: Dict[str, Any] = None):

        """
        Configure what koji API calls should return.

        Args:
            client_responses: Dict mapping method names to return values for ClientSession calls
            config_responses: Dict mapping profile names to config dicts for koji.read_config

        Example:
            self.configure_koji_responses(
                client_responses=['getTag', {'name': 'test-tag', 'arches': 'x86_64'}}],
                config_responses={'koji': {'server': 'http://test-koji.example.com'}}
            )
        """

        for resp in client_responses:
            self.client_responses.setdefault(resp[0], []).append(resp[1])

        if config_responses:
            def config_side_effect(profile_name, *args, **kwargs):
                return config_responses.get(profile_name, {})
            self.read_config_mock.side_effect = config_side_effect


    def queue_client_response(self, method_name: str, response: Any):
        """
        Queue up a response for a specific method in the next multicall execution.
        """
        self.client_responses.setdefault(method_name, []).append(response)


    queue_multicall_response = queue_client_response


# The end.

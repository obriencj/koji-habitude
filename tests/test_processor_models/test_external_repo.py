"""
koji-habitude - test_processor_models.test_external_repo

Unit tests for processor integration with external repository models and change reporting.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

from unittest import TestCase
from unittest.mock import Mock

from koji_habitude.models import ExternalRepo
from koji_habitude.processor import Processor, ProcessorState, ProcessorSummary

from . import (
    MulticallMocking,
    create_empty_resolver,
    create_solver_with_objects,
    create_test_koji_session,
)


def create_test_external_repo(name: str, url: str) -> ExternalRepo:
    """
    Create a test external repository with the specified parameters.

    Args:
        name: External repository name
        url: External repository URL (must be http/https)

    Returns:
        ExternalRepo object for testing
    """
    return ExternalRepo(
        name=name,
        url=url,
        filename='test.yaml',
        lineno=1
    )


class TestProcessorExternalRepoBehavior(MulticallMocking, TestCase):

    def test_external_repo_creation(self):
        """Test creating a new external repository."""
        external_repo = create_test_external_repo('new-repo', 'https://example.com/repo')
        solver = create_solver_with_objects([external_repo])
        mock_session = create_test_koji_session()

        get_repo_mock = Mock()
        get_repo_mock.return_value = None

        create_mock = Mock()
        create_mock.return_value = None

        self.queue_client_response('getExternalRepo', get_repo_mock)
        self.queue_client_response('createExternalRepo', create_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_repo_mock.assert_called_once_with('new-repo', strict=False)
        create_mock.assert_called_once_with('new-repo', 'https://example.com/repo')

    def test_external_repo_update_url(self):
        """Test updating an existing external repository's URL."""
        external_repo = create_test_external_repo('existing-repo', 'https://new.example.com/repo')
        solver = create_solver_with_objects([external_repo])
        mock_session = create_test_koji_session()

        # Mock the getExternalRepo call to return existing repo with different URL
        get_repo_mock = Mock()
        get_repo_mock.return_value = {
            'name': 'existing-repo',
            'url': 'https://old.example.com/repo'
        }

        edit_mock = Mock()
        edit_mock.return_value = None

        self.queue_client_response('getExternalRepo', get_repo_mock)
        self.queue_client_response('editExternalRepo', edit_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_repo_mock.assert_called_once_with('existing-repo', strict=False)
        edit_mock.assert_called_once_with('existing-repo', url='https://new.example.com/repo')

    def test_external_repo_no_changes_needed(self):
        """Test external repository that already matches desired state."""
        external_repo = create_test_external_repo('existing-repo', 'https://example.com/repo')
        solver = create_solver_with_objects([external_repo])
        mock_session = create_test_koji_session()

        # Mock the getExternalRepo call to return repo that already matches desired state
        get_repo_mock = Mock()
        get_repo_mock.return_value = {
            'name': 'existing-repo',
            'url': 'https://example.com/repo'  # Already matches
        }

        self.queue_client_response('getExternalRepo', get_repo_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_repo_mock.assert_called_once_with('existing-repo', strict=False)

    def test_external_repo_http_url(self):
        """Test creating an external repository with HTTP URL."""
        external_repo = create_test_external_repo('http-repo', 'http://example.com/repo')
        solver = create_solver_with_objects([external_repo])
        mock_session = create_test_koji_session()

        get_repo_mock = Mock()
        get_repo_mock.return_value = None

        create_mock = Mock()
        create_mock.return_value = None

        self.queue_client_response('getExternalRepo', get_repo_mock)
        self.queue_client_response('createExternalRepo', create_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        result = processor.step()
        self.assertTrue(result)  # Should process 1 object
        self.assertEqual(processor.state, ProcessorState.READY_CHUNK)

        get_repo_mock.assert_called_once_with('http-repo', strict=False)
        create_mock.assert_called_once_with('http-repo', 'http://example.com/repo')

    def test_processor_summary_with_multiple_external_repos(self):
        """Test that the processor summary is correct with multiple external repositories."""
        external_repos = [
            create_test_external_repo('repo1', 'https://example1.com/repo'),
            create_test_external_repo('repo2', 'https://example2.com/repo')
        ]
        solver = create_solver_with_objects(external_repos)
        mock_session = create_test_koji_session()

        # Mock getExternalRepo calls to return None (repos don't exist)
        get_repo1_mock = Mock()
        get_repo1_mock.return_value = None

        get_repo2_mock = Mock()
        get_repo2_mock.return_value = None

        # Mock createExternalRepo calls for repo creation
        create1_mock = Mock()
        create1_mock.return_value = None

        create2_mock = Mock()
        create2_mock.return_value = None

        # Queue responses for both repos
        self.queue_client_response('getExternalRepo', get_repo1_mock)
        self.queue_client_response('createExternalRepo', create1_mock)

        self.queue_client_response('getExternalRepo', get_repo2_mock)
        self.queue_client_response('createExternalRepo', create2_mock)

        processor = Processor(
            koji_session=mock_session,
            dataseries=solver,
            resolver=create_empty_resolver(),
            chunk_size=10
        )

        summary = processor.run()
        self.assertIsInstance(summary, ProcessorSummary)
        self.assertEqual(summary.total_objects, 2)
        self.assertEqual(summary.steps_completed, 1)
        self.assertEqual(summary.state, ProcessorState.EXHAUSTED)

        # Verify all calls were made
        get_repo1_mock.assert_called_once_with('repo1', strict=False)
        get_repo2_mock.assert_called_once_with('repo2', strict=False)
        create1_mock.assert_called_once_with('repo1', 'https://example1.com/repo')
        create2_mock.assert_called_once_with('repo2', 'https://example2.com/repo')


# The end.

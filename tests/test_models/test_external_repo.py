"""
koji-habitude - test_external_repo

Unit tests for koji_habitude.models.ExternalRepo.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

import unittest

from koji_habitude.models import ExternalRepo


class TestExternalRepoModel(unittest.TestCase):
    """
    Test the ExternalRepo model.
    """

    def test_external_repo_creation(self):
        """
        Test ExternalRepo creation with valid URL.
        """

        data = {
            'type': 'external-repo',
            'name': 'test-repo',
            'url': 'https://example.com/repo'
        }
        repo = ExternalRepo.from_dict(data)

        self.assertEqual(repo.typename, 'external-repo')
        self.assertEqual(repo.name, 'test-repo')
        self.assertEqual(repo.url, 'https://example.com/repo')
        self.assertFalse(repo.can_split())

    def test_external_repo_creation_http_url(self):
        """
        Test ExternalRepo creation with HTTP URL.
        """

        data = {
            'type': 'external-repo',
            'name': 'test-repo',
            'url': 'http://example.com/repo'
        }
        repo = ExternalRepo.from_dict(data)

        self.assertEqual(repo.url, 'http://example.com/repo')

    def test_external_repo_invalid_url_pattern(self):
        """
        Test ExternalRepo creation with invalid URL pattern.
        """

        data = {
            'type': 'external-repo',
            'name': 'test-repo',
            'url': 'ftp://example.com/repo'
        }

        with self.assertRaises(ValueError):
            ExternalRepo.from_dict(data)

    def test_external_repo_dependency_keys(self):
        """
        Test ExternalRepo has no dependencies.
        """

        data = {
            'type': 'external-repo',
            'name': 'test-repo',
            'url': 'https://example.com/repo'
        }
        repo = ExternalRepo.from_dict(data)

        deps = repo.dependency_keys()
        self.assertEqual(deps, ())


# The end.

"""
koji-habitude - test_archive_type

Unit tests for koji_habitude.models.ArchiveType.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 4.5 Sonnet via Cursor
"""

import unittest

from pydantic import ValidationError

from koji_habitude.models import ArchiveType


class TestArchiveTypeModel(unittest.TestCase):
    """
    Test the ArchiveType model.
    """

    def test_archive_type_creation_with_extensions(self):
        """
        Test ArchiveType creation with required extensions field.
        """

        data = {
            'type': 'archive-type',
            'name': 'jar',
            'extensions': ['jar']
        }
        archive_type = ArchiveType.from_dict(data)

        self.assertEqual(archive_type.typename, 'archive-type')
        self.assertEqual(archive_type.name, 'jar')
        self.assertEqual(archive_type.extensions, ['jar'])
        self.assertEqual(archive_type.description, '')
        self.assertIsNone(archive_type.compression)
        self.assertFalse(archive_type.can_split())

    def test_archive_type_creation_with_all_fields(self):
        """
        Test ArchiveType creation with all fields specified.
        """

        data = {
            'type': 'archive-type',
            'name': 'tar',
            'extensions': ['tar'],
            'description': 'TAR archive',
            'compression-type': 'tar'
        }
        archive_type = ArchiveType.from_dict(data)

        self.assertEqual(archive_type.name, 'tar')
        self.assertEqual(archive_type.extensions, ['tar'])
        self.assertEqual(archive_type.description, 'TAR archive')
        self.assertEqual(archive_type.compression, 'tar')

    def test_archive_type_extensions_strip_leading_dots(self):
        """
        Test that extensions validator strips leading dots.
        """

        data = {
            'type': 'archive-type',
            'name': 'test',
            'extensions': ['.jar', '.war', 'ear']
        }
        archive_type = ArchiveType.from_dict(data)

        # Should strip leading dots from .jar and .war
        self.assertIn('jar', archive_type.extensions)
        self.assertIn('war', archive_type.extensions)
        self.assertIn('ear', archive_type.extensions)
        # Should not have any extensions with leading dots
        for ext in archive_type.extensions:
            self.assertFalse(ext.startswith('.'))

    def test_archive_type_extensions_deduplicate(self):
        """
        Test that extensions validator deduplicates extensions.
        """

        data = {
            'type': 'archive-type',
            'name': 'test',
            'extensions': ['jar', 'jar', 'war', 'jar']
        }
        archive_type = ArchiveType.from_dict(data)

        # Should deduplicate to unique values
        self.assertEqual(len(archive_type.extensions), 2)
        self.assertIn('jar', archive_type.extensions)
        self.assertIn('war', archive_type.extensions)

    def test_archive_type_extensions_strip_and_deduplicate(self):
        """
        Test that extensions validator both strips dots and deduplicates.
        """

        data = {
            'type': 'archive-type',
            'name': 'test',
            'extensions': ['.jar', 'jar', '.jar', 'war', '.war']
        }
        archive_type = ArchiveType.from_dict(data)

        # .jar and jar should become the same after stripping
        self.assertEqual(len(archive_type.extensions), 2)
        self.assertIn('jar', archive_type.extensions)
        self.assertIn('war', archive_type.extensions)

    def test_archive_type_compression_type_tar(self):
        """
        Test ArchiveType with compression-type set to 'tar'.
        """

        data = {
            'type': 'archive-type',
            'name': 'tar',
            'extensions': ['tar'],
            'compression-type': 'tar'
        }
        archive_type = ArchiveType.from_dict(data)

        self.assertEqual(archive_type.compression, 'tar')

    def test_archive_type_compression_type_zip(self):
        """
        Test ArchiveType with compression-type set to 'zip'.
        """

        data = {
            'type': 'archive-type',
            'name': 'zip',
            'extensions': ['zip'],
            'compression-type': 'zip'
        }
        archive_type = ArchiveType.from_dict(data)

        self.assertEqual(archive_type.compression, 'zip')

    def test_archive_type_compression_type_none(self):
        """
        Test ArchiveType with no compression-type (defaults to None).
        """

        data = {
            'type': 'archive-type',
            'name': 'jar',
            'extensions': ['jar']
        }
        archive_type = ArchiveType.from_dict(data)

        self.assertIsNone(archive_type.compression)

    def test_archive_type_compression_type_invalid(self):
        """
        Test that invalid compression-type values are rejected.
        """

        data = {
            'type': 'archive-type',
            'name': 'test',
            'extensions': ['test'],
            'compression-type': 'gzip'  # Invalid, only 'tar' and 'zip' allowed
        }

        with self.assertRaises(ValidationError) as cm:
            ArchiveType.from_dict(data)

        # Check that the error is about invalid literal value
        self.assertIn('compression', str(cm.exception).lower())

    def test_archive_type_description_field(self):
        """
        Test ArchiveType description field.
        """

        # With description
        data = {
            'type': 'archive-type',
            'name': 'jar',
            'extensions': ['jar'],
            'description': 'Java Archive'
        }
        archive_type = ArchiveType.from_dict(data)
        self.assertEqual(archive_type.description, 'Java Archive')

        # Without description (defaults to empty string)
        data = {
            'type': 'archive-type',
            'name': 'war',
            'extensions': ['war']
        }
        archive_type = ArchiveType.from_dict(data)
        self.assertEqual(archive_type.description, '')

    def test_archive_type_multiple_extensions(self):
        """
        Test ArchiveType with multiple extensions.
        """

        data = {
            'type': 'archive-type',
            'name': 'tarball',
            'extensions': ['tar.gz', 'tgz', 'tar.bz2', 'tbz2'],
            'compression-type': 'tar'
        }
        archive_type = ArchiveType.from_dict(data)

        self.assertEqual(len(archive_type.extensions), 4)
        self.assertIn('tar.gz', archive_type.extensions)
        self.assertIn('tgz', archive_type.extensions)
        self.assertIn('tar.bz2', archive_type.extensions)
        self.assertIn('tbz2', archive_type.extensions)

    def test_archive_type_dependency_keys(self):
        """
        Test ArchiveType has no dependencies.
        """

        data = {
            'type': 'archive-type',
            'name': 'jar',
            'extensions': ['jar']
        }
        archive_type = ArchiveType.from_dict(data)

        deps = archive_type.dependency_keys()
        self.assertEqual(deps, ())


# The end.

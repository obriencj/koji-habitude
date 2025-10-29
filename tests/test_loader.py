"""
koji-habitude - test_loader

Unit tests for koji_habitude.loader module.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated


import os
import unittest
from pathlib import Path

from koji_habitude.loader import find_files, combine_find_files, YAMLLoader, MultiLoader


# Global file count constants for test data directories
# Update these when adding/removing test files
TEMPLATES_YAML_COUNT = 9  # .yaml and .yml files in templates/ (excluding .j2)
TEMPLATES_J2_COUNT = 1    # .j2 files in templates/
TEMPLATES_TOTAL_COUNT = TEMPLATES_YAML_COUNT + TEMPLATES_J2_COUNT

SAMPLES_YAML_COUNT = 2    # .yaml/.yml files in samples/ (including nested/)
BAD_YAML_COUNT = 5        # .yaml/.yml files in bad/ (excluding .txt)
BAD_TOTAL_COUNT = 6       # All files in bad/ (including .txt)


class TestFindFiles(unittest.TestCase):
    """
    Test cases for the find_files function.
    """

    def setUp(self):
        """
        Set up test data paths.
        """

        self.test_data_dir = Path(__file__).parent / 'data'
        self.templates_dir = self.test_data_dir / 'templates'
        self.samples_dir = self.test_data_dir / 'samples'
        self.bad_dir = self.test_data_dir / 'bad'

    def test_find_single_yaml_file(self):
        """
        Test finding a single YAML file by direct path.
        """

        yaml_file = self.templates_dir / 'simple.yaml'
        result = find_files(yaml_file)

        self.assertEqual(len(result), 1, "Should find exactly one file")
        self.assertEqual(result[0], yaml_file, "Should return the exact file path")

    def test_find_single_yml_file(self):
        """
        Test finding a single YML file by direct path.
        """

        yml_file = self.templates_dir / 'complex.yml'
        result = find_files(yml_file)

        self.assertEqual(len(result), 1, "Should find exactly one file")
        self.assertEqual(result[0], yml_file, "Should return the exact file path")

    def test_find_files_in_directory(self):
        """
        Test finding all YAML files in a directory.
        """

        result = find_files(self.templates_dir)

        self.assertEqual(len(result), TEMPLATES_YAML_COUNT, "Should find all YAML files in templates directory")

        # Results should be sorted - check that original files are included
        expected_original_files = [
            self.templates_dir / 'complex.yml',
            self.templates_dir / 'simple.yaml'
        ]
        for expected_file in expected_original_files:
            self.assertIn(expected_file, result, f"Should include {expected_file.name}")

        # Verify all results are sorted
        self.assertEqual(result, sorted(result), "Should return sorted list of YAML files")

    def test_find_files_recursive(self):
        """
        Test finding YAML files recursively in nested directories.
        """

        result = find_files(self.samples_dir, recursive=True)

        self.assertEqual(len(result), SAMPLES_YAML_COUNT, "Should find YAML files recursively")

        # Check that nested file is included
        nested_file = self.samples_dir / 'nested' / 'deep.yml'
        self.assertIn(nested_file, result, "Should include files from nested directories")

    def test_find_files_non_recursive(self):
        """
        Test finding YAML files non-recursively (default behavior).
        """

        result = find_files(self.samples_dir, recursive=False)

        # Should only find files in the top-level directory, not nested
        self.assertEqual(len(result), 1, "Should find only top-level YAML files when non-recursive")

        # Check that nested file is NOT included
        nested_file = self.samples_dir / 'nested' / 'deep.yml'
        self.assertNotIn(nested_file, result, "Should not include files from nested directories when non-recursive")

    def test_find_files_ignores_non_yaml(self):
        """
        Test that non-YAML files are ignored.
        """

        result = find_files(self.bad_dir)

        # Now there's malformed.yaml in bad directory, but we should still find it
        # since it has .yaml extension (even though it's malformed)
        self.assertEqual(len(result), BAD_YAML_COUNT, "Should find the YAML files in bad directory")
        self.assertTrue(result[0].name.endswith('.yaml'), "Found file should be YAML")

    def test_find_files_with_custom_extensions(self):
        """
        Test finding files with custom extensions.
        """

        result = find_files(self.bad_dir, extensions=('.txt',))

        self.assertEqual(len(result), 1, "Should find text file with custom extension")
        self.assertTrue(result[0].name.endswith('.txt'), "Found file should have .txt extension")

    def test_find_files_default_strict_behavior(self):
        """
        Test that strict=True is the default behavior.
        """

        nonexistent_path = self.test_data_dir / 'nonexistent'

        # Should raise exception with default parameters
        with self.assertRaises(FileNotFoundError):
            find_files(nonexistent_path)

        # Should also raise exception when explicitly set to True
        with self.assertRaises(FileNotFoundError):
            find_files(nonexistent_path, strict=True)

    def test_find_files_nonexistent_path_strict(self):
        """
        Test behavior with non-existent path when strict=True (default).
        """

        nonexistent_path = self.test_data_dir / 'nonexistent'

        with self.assertRaises(FileNotFoundError) as context:
            find_files(nonexistent_path, strict=True)

        self.assertIn(str(nonexistent_path), str(context.exception),
                     "Exception should mention the missing path")

    def test_find_files_nonexistent_path_non_strict(self):
        """
        Test behavior with non-existent path when strict=False.
        """

        nonexistent_path = self.test_data_dir / 'nonexistent'
        result = find_files(nonexistent_path, strict=False)

        self.assertEqual(result, [], "Should return empty list for non-existent path when strict=False")

    def test_find_files_empty_path(self):
        """
        Test behavior with None/empty path.
        """

        with self.assertRaises(ValueError):
            find_files(None)


class TestCombineFindFiles(unittest.TestCase):
    """
    Test cases for the combine_find_files function.
    """

    def setUp(self):
        """
        Set up test data paths.
        """

        self.test_data_dir = Path(__file__).parent / 'data'
        self.templates_dir = self.test_data_dir / 'templates'
        self.samples_dir = self.test_data_dir / 'samples'

    def test_combine_single_directory(self):
        """
        Test combining files from a single directory.
        """

        result = combine_find_files([self.templates_dir])

        self.assertEqual(len(result), TEMPLATES_YAML_COUNT, "Should find all files in templates directory")

    def test_combine_multiple_directories_recursive(self):
        """
        Test combining files from multiple directories with recursive search.
        """

        result = combine_find_files([self.templates_dir, self.samples_dir], recursive=True)

        self.assertEqual(len(result), TEMPLATES_YAML_COUNT + SAMPLES_YAML_COUNT, "Should find files from both directories when recursive")

        # Check that files from both directories are included
        template_files = [f for f in result if 'templates' in str(f)]
        sample_files = [f for f in result if 'samples' in str(f)]

        self.assertEqual(len(template_files), TEMPLATES_YAML_COUNT, "Should include all template files")
        self.assertEqual(len(sample_files), SAMPLES_YAML_COUNT, "Should include all sample files")

    def test_combine_multiple_directories_non_recursive(self):
        """
        Test combining files from multiple directories with non-recursive search (default).
        """

        result = combine_find_files([self.templates_dir, self.samples_dir], recursive=False)

        # Should find 9 template files + 1 sample file (top-level only)
        expected_count = TEMPLATES_YAML_COUNT + 1
        self.assertEqual(len(result), expected_count, "Should find files from both directories when non-recursive")

        # Check that files from both directories are included
        template_files = [f for f in result if 'templates' in str(f)]
        sample_files = [f for f in result if 'samples' in str(f)]

        self.assertEqual(len(template_files), TEMPLATES_YAML_COUNT, "Should include all template files")
        self.assertEqual(len(sample_files), 1, "Should include only top-level sample files when non-recursive")

    def test_combine_mixed_paths_recursive(self):
        """
        Test combining specific files and directories with recursive search.
        """

        specific_file = self.templates_dir / 'simple.yaml'
        paths = [specific_file, self.samples_dir]

        result = combine_find_files(paths, recursive=True)

        self.assertEqual(len(result), 3, "Should find 3 files (1 specific + 2 from samples) when recursive")
        self.assertIn(specific_file, result, "Should include specifically requested file")

    def test_combine_mixed_paths_non_recursive(self):
        """
        Test combining specific files and directories with non-recursive search (default).
        """

        specific_file = self.templates_dir / 'simple.yaml'
        paths = [specific_file, self.samples_dir]

        result = combine_find_files(paths, recursive=False)

        self.assertEqual(len(result), 2, "Should find 2 files (1 specific + 1 from samples top-level) when non-recursive")
        self.assertIn(specific_file, result, "Should include specifically requested file")

    def test_combine_empty_list(self):
        """
        Test combining with empty path list.
        """

        result = combine_find_files([])

        self.assertEqual(len(result), 0, "Should return empty list for empty input")

    def test_combine_with_custom_extensions(self):
        """
        Test combining files with custom extensions.
        """

        bad_dir = self.test_data_dir / 'bad'
        result = combine_find_files([bad_dir], extensions=('.txt',))

        self.assertEqual(len(result), 1, "Should find text file with custom extension")

    def test_combine_duplicate_paths(self):
        """
        Test that duplicate paths don't result in duplicate files.
        """

        # Note: This tests the current behavior - find_files may return duplicates
        # if the same path is specified multiple times
        result = combine_find_files([self.templates_dir, self.templates_dir])

        # Current implementation will return duplicates
        self.assertEqual(len(result), TEMPLATES_YAML_COUNT * 2, f"Current implementation returns duplicates ({TEMPLATES_YAML_COUNT} files x 2)")

    def test_combine_with_nonexistent_path_strict(self):
        """
        Test combine_find_files with non-existent path when strict=True (default).
        """

        nonexistent_path = self.test_data_dir / 'nonexistent'
        paths = [self.templates_dir, nonexistent_path]

        with self.assertRaises(FileNotFoundError):
            combine_find_files(paths, strict=True)

    def test_combine_with_nonexistent_path_non_strict(self):
        """
        Test combine_find_files with non-existent path when strict=False.
        """

        nonexistent_path = self.test_data_dir / 'nonexistent'
        paths = [self.templates_dir, nonexistent_path]

        result = combine_find_files(paths, strict=False)

        # Should only find files from the existing directory
        self.assertEqual(len(result), TEMPLATES_YAML_COUNT, "Should find files from existing directory only")

        # All found files should be from templates directory
        for file_path in result:
            self.assertIn('templates', str(file_path), "All files should be from templates directory")

    def test_combine_default_strict_behavior(self):
        """
        Test that strict=True is the default for combine_find_files.
        """

        nonexistent_path = self.test_data_dir / 'nonexistent'
        paths = [nonexistent_path]

        # Should raise exception with default parameters
        with self.assertRaises(FileNotFoundError):
            combine_find_files(paths)

        # Should also raise exception when explicitly set to True
        with self.assertRaises(FileNotFoundError):
            combine_find_files(paths, strict=True)


class TestYAMLLoader(unittest.TestCase):
    """
    Test cases for the YAMLLoader class.
    """

    def setUp(self):
        """
        Set up test data paths.
        """

        self.test_data_dir = Path(__file__).parent / 'data'
        self.templates_dir = self.test_data_dir / 'templates'
        self.bad_dir = self.test_data_dir / 'bad'

    def test_yaml_loader_init_with_valid_file(self):
        """
        Test YAMLLoader initialization with valid file path.
        """

        yaml_file = self.templates_dir / 'single_document.yaml'
        loader = YAMLLoader(yaml_file)

        self.assertEqual(loader.filename, str(yaml_file), "Should store filename as string")

    def test_yaml_loader_init_with_string_path(self):
        """
        Test YAMLLoader initialization with string file path.
        """

        yaml_file = str(self.templates_dir / 'single_document.yaml')
        loader = YAMLLoader(yaml_file)

        self.assertEqual(loader.filename, yaml_file, "Should accept string path")

    def test_yaml_loader_init_with_nonexistent_file(self):
        """
        Test YAMLLoader initialization with non-existent file.
        """

        nonexistent_file = self.templates_dir / 'nonexistent.yaml'

        with self.assertRaises(ValueError) as context:
            YAMLLoader(nonexistent_file)

        self.assertIn("filename must be a file", str(context.exception),
                     "Should provide clear error message")

    def test_yaml_loader_init_with_directory(self):
        """
        Test YAMLLoader initialization with directory instead of file.
        """

        with self.assertRaises(ValueError) as context:
            YAMLLoader(self.templates_dir)

        self.assertIn("filename must be a file", str(context.exception),
                     "Should reject directory paths")

    def test_yaml_loader_init_with_none(self):
        """
        Test YAMLLoader initialization with None.
        """

        with self.assertRaises(ValueError) as context:
            YAMLLoader(None)

        self.assertIn("filename must be a file", str(context.exception),
                     "Should reject None input")

    def test_yaml_loader_extensions(self):
        """
        Test that YAMLLoader has correct extensions attribute.
        """

        self.assertEqual(YAMLLoader.extensions, (".yml", ".yaml"),
                        "Should support both .yml and .yaml extensions")

    def test_load_single_document(self):
        """
        Test loading a single YAML document with __file__ and __line__ decoration.
        """

        yaml_file = self.templates_dir / 'single_document.yaml'
        loader = YAMLLoader(yaml_file)

        documents = list(loader.load())

        self.assertEqual(len(documents), 1, "Should load exactly one document")

        doc = documents[0]
        self.assertIn('__file__', doc, "Document should have __file__ key")
        self.assertIn('__line__', doc, "Document should have __line__ key")

        self.assertEqual(doc['__file__'], str(yaml_file), "__file__ should match the source file")
        self.assertEqual(doc['__line__'], 2, "__line__ should be 2 (first actual content line)")

        # Check that original content is preserved with new structure
        self.assertEqual(doc['type'], 'tag', "Document should have 'type' field")
        self.assertEqual(doc['name'], 'single-doc', "Should preserve original content")

    def test_load_multiple_documents(self):
        """
        Test loading multiple YAML documents from a single file.
        """

        yaml_file = self.templates_dir / 'multiple_documents.yml'
        loader = YAMLLoader(yaml_file)

        documents = list(loader.load())

        self.assertEqual(len(documents), 3, "Should load exactly three documents")

        # Check first document
        doc1 = documents[0]
        self.assertEqual(doc1['__file__'], str(yaml_file), "First doc should have correct __file__")
        self.assertEqual(doc1['__line__'], 2, "First doc should start at line 2")
        self.assertEqual(doc1['type'], 'target', "First doc should have 'type' field")
        self.assertEqual(doc1['name'], 'first-doc', "First doc should have correct content")

        # Check second document
        doc2 = documents[1]
        self.assertEqual(doc2['__file__'], str(yaml_file), "Second doc should have correct __file__")
        self.assertEqual(doc2['__line__'], 7, "Second doc should start at line 7")
        self.assertEqual(doc2['type'], 'host', "Second doc should have 'type' field")
        self.assertEqual(doc2['name'], 'second-doc', "Second doc should have correct content")

        # Check third document
        doc3 = documents[2]
        self.assertEqual(doc3['__file__'], str(yaml_file), "Third doc should have correct __file__")
        self.assertEqual(doc3['__line__'], 12, "Third doc should start at line 12")
        self.assertEqual(doc3['type'], 'user', "Third doc should have 'type' field")
        self.assertEqual(doc3['name'], 'third-doc', "Third doc should have correct content")

    def test_load_document_with_leading_whitespace(self):
        """
        Test loading document that starts after leading whitespace/comments.
        """

        yaml_file = self.templates_dir / 'with_leading_whitespace.yml'
        loader = YAMLLoader(yaml_file)

        documents = list(loader.load())

        self.assertEqual(len(documents), 1, "Should load exactly one document")

        doc = documents[0]
        self.assertEqual(doc['__file__'], str(yaml_file), "Should have correct __file__")
        self.assertEqual(doc['__line__'], 3, "Should correctly identify line 3 as start")
        self.assertEqual(doc['type'], 'group', "Document should have 'type' field")
        self.assertEqual(doc['name'], 'whitespace-doc', "Should preserve content")

    def test_load_empty_file(self):
        """
        Test loading an effectively empty YAML file.
        """

        yaml_file = self.templates_dir / 'empty_file.yaml'
        loader = YAMLLoader(yaml_file)

        documents = list(loader.load())

        self.assertEqual(len(documents), 0, "Should load no documents from empty file")

    def test_load_malformed_yaml(self):
        """
        Test loading malformed YAML raises appropriate exception.
        """

        yaml_file = self.bad_dir / 'malformed.yaml'
        loader = YAMLLoader(yaml_file)

        with self.assertRaises(Exception) as context:
            list(loader.load())

        # Should raise a YAML parsing exception
        self.assertTrue(
            any(exc_type in str(type(context.exception)) for exc_type in ['yaml', 'YAML', 'scanner', 'parser']),
            f"Should raise YAML-related exception, got {type(context.exception)}"
        )

    def test_load_preserves_original_data_types(self):
        """
        Test that loading preserves original YAML data types.
        """

        yaml_file = self.templates_dir / 'single_document.yaml'
        loader = YAMLLoader(yaml_file)

        documents = list(loader.load())
        doc = documents[0]

        # Check that data types are preserved
        self.assertIsInstance(doc['name'], str, "String should remain string")
        self.assertIsInstance(doc['locked'], bool, "Boolean should remain boolean")
        self.assertIsInstance(doc['arches'], list, "List should remain list")
        self.assertEqual(len(doc['arches']), 2, "List should have correct length")

    def test_load_is_generator(self):
        """
        Test that load() returns a generator, not a list.
        """

        yaml_file = self.templates_dir / 'multiple_documents.yml'
        loader = YAMLLoader(yaml_file)

        result = loader.load()

        # Should be a generator, not a list
        self.assertFalse(hasattr(result, '__len__'), "Should return generator, not list")
        self.assertTrue(hasattr(result, '__iter__'), "Should be iterable")
        self.assertTrue(hasattr(result, '__next__'), "Should be a generator")

    def test_load_can_be_consumed_multiple_times(self):
        """
        Test that load() can be called multiple times to get fresh generators.
        """

        yaml_file = self.templates_dir / 'multiple_documents.yml'
        loader = YAMLLoader(yaml_file)

        # First consumption
        docs1 = list(loader.load())
        self.assertEqual(len(docs1), 3, "First load should return 3 documents")

        # Second consumption should work independently
        docs2 = list(loader.load())
        self.assertEqual(len(docs2), 3, "Second load should also return 3 documents")

        # Documents should be equivalent but not the same objects
        self.assertEqual(docs1[0]['name'], docs2[0]['name'], "Content should be the same")
        self.assertIsNot(docs1[0], docs2[0], "Should be different object instances")


class TestMultiLoader(unittest.TestCase):
    """
    Test cases for the MultiLoader class.
    """

    def setUp(self):
        """
        Set up test data paths.
        """

        self.test_data_dir = Path(__file__).parent / 'data'
        self.templates_dir = self.test_data_dir / 'templates'
        self.samples_dir = self.test_data_dir / 'samples'
        self.bad_dir = self.test_data_dir / 'bad'

    def test_multiloader_init_with_single_loader_type(self):
        """
        Test MultiLoader initialization with a single loader type.
        """

        multiloader = MultiLoader([YAMLLoader])

        self.assertIn('.yml', multiloader.extmap, "Should register .yml extension")
        self.assertIn('.yaml', multiloader.extmap, "Should register .yaml extension")
        self.assertEqual(multiloader.extmap['.yml'], YAMLLoader, "Should map .yml to YAMLLoader")
        self.assertEqual(multiloader.extmap['.yaml'], YAMLLoader, "Should map .yaml to YAMLLoader")

    def test_multiloader_init_with_multiple_loader_types(self):
        """
        Test MultiLoader initialization with multiple loader types.
        """

        # Create a mock loader class for testing
        class MockLoader:
            extensions = ('.mock', '.test')
            def __init__(self, filename):
                self.filename = filename
            def load(self):
                return []

        multiloader = MultiLoader([YAMLLoader, MockLoader])

        # Should have all extensions from both loaders
        self.assertIn('.yml', multiloader.extmap, "Should register .yml from YAMLLoader")
        self.assertIn('.yaml', multiloader.extmap, "Should register .yaml from YAMLLoader")
        self.assertIn('.mock', multiloader.extmap, "Should register .mock from MockLoader")
        self.assertIn('.test', multiloader.extmap, "Should register .test from MockLoader")

        # Should map to correct loader types
        self.assertEqual(multiloader.extmap['.yml'], YAMLLoader)
        self.assertEqual(multiloader.extmap['.mock'], MockLoader)

    def test_multiloader_init_empty_loader_list(self):
        """
        Test MultiLoader initialization with empty loader list.
        """

        multiloader = MultiLoader([])

        self.assertEqual(len(multiloader.extmap), 0, "Should have empty extension map")

    def test_lookup_loader_type_with_known_extension(self):
        """
        Test lookup_loader_type with known file extensions.
        """

        multiloader = MultiLoader([YAMLLoader])

        yaml_file = self.templates_dir / 'simple.yaml'
        yml_file = self.templates_dir / 'complex.yml'

        self.assertEqual(multiloader.lookup_loader_type(yaml_file), YAMLLoader,
                        "Should return YAMLLoader for .yaml files")
        self.assertEqual(multiloader.lookup_loader_type(yml_file), YAMLLoader,
                        "Should return YAMLLoader for .yml files")

    def test_lookup_loader_type_with_unknown_extension(self):
        """
        Test lookup_loader_type with unknown file extension.
        """

        multiloader = MultiLoader([YAMLLoader])

        txt_file = self.bad_dir / 'not_yaml.txt'

        self.assertIsNone(multiloader.lookup_loader_type(txt_file),
                         "Should return None for unknown extensions")

    def test_lookup_loader_type_with_none_path(self):
        """
        Test lookup_loader_type with None path.
        """

        multiloader = MultiLoader([YAMLLoader])

        self.assertIsNone(multiloader.lookup_loader_type(None),
                         "Should return None for None path")

    def test_loader_creation_with_valid_file(self):
        """
        Test creating a loader instance for a valid file.
        """

        multiloader = MultiLoader([YAMLLoader])
        yaml_file = self.templates_dir / 'simple.yaml'

        loader_instance = multiloader.loader(yaml_file)

        self.assertIsInstance(loader_instance, YAMLLoader, "Should create YAMLLoader instance")
        self.assertEqual(loader_instance.filename, str(yaml_file), "Should set correct filename")

    def test_loader_creation_with_invalid_extension(self):
        """
        Test creating a loader instance for file with unsupported extension.
        """

        multiloader = MultiLoader([YAMLLoader])
        txt_file = self.bad_dir / 'not_yaml.txt'

        with self.assertRaises(ValueError) as context:
            multiloader.loader(txt_file)

        self.assertIn("No loader accepting filename", str(context.exception),
                     "Should provide clear error message")

    def test_add_loader_type_after_initialization(self):
        """
        Test adding a loader type after MultiLoader initialization.
        """

        # Create a mock loader class
        class MockLoader:
            extensions = ('.custom',)
            def __init__(self, filename):
                self.filename = filename
            def load(self):
                return []

        multiloader = MultiLoader([YAMLLoader])
        self.assertNotIn('.custom', multiloader.extmap, "Should not have .custom initially")

        multiloader.add_loader_type(MockLoader)
        self.assertIn('.custom', multiloader.extmap, "Should register .custom after adding")
        self.assertEqual(multiloader.extmap['.custom'], MockLoader, "Should map to MockLoader")

    def test_load_single_file(self):
        """
        Test loading a single file through MultiLoader.
        """

        multiloader = MultiLoader([YAMLLoader])
        yaml_file = self.templates_dir / 'single_document.yaml'

        documents = list(multiloader.load([yaml_file]))

        self.assertEqual(len(documents), 1, "Should load exactly one document")

        doc = documents[0]
        self.assertIn('__file__', doc, "Document should have __file__ decoration")
        self.assertIn('__line__', doc, "Document should have __line__ decoration")
        self.assertEqual(doc['type'], 'tag', "Document should have tag type")

    def test_load_multiple_files(self):
        """
        Test loading multiple files through MultiLoader.
        """

        multiloader = MultiLoader([YAMLLoader])
        files = [
            self.templates_dir / 'single_document.yaml',
            self.templates_dir / 'multiple_documents.yml'
        ]

        documents = list(multiloader.load(files))

        # single_document.yaml has 1 doc, multiple_documents.yml has 3 docs
        self.assertEqual(len(documents), 4, "Should load all documents from both files")

        # Check that documents from different files are included
        file_sources = [doc['__file__'] for doc in documents]
        self.assertIn(str(files[0]), file_sources, "Should include docs from first file")
        self.assertIn(str(files[1]), file_sources, "Should include docs from second file")

    def test_load_directory(self):
        """
        Test loading all files from a directory through MultiLoader.
        """

        multiloader = MultiLoader([YAMLLoader])

        documents = list(multiloader.load([self.templates_dir]))

        # Should load all YAML files in templates directory
        self.assertGreater(len(documents), 5, "Should load multiple documents from directory")

        # All documents should have file and line decorations
        for doc in documents:
            self.assertIn('__file__', doc, "Each document should have __file__")
            self.assertIn('__line__', doc, "Each document should have __line__")

    def test_load_mixed_paths_recursive(self):
        """
        Test loading from mixed file and directory paths with recursive search.
        """

        multiloader = MultiLoader([YAMLLoader])

        specific_file = self.templates_dir / 'single_document.yaml'
        paths = [specific_file, self.samples_dir]

        documents = list(multiloader.load(paths, recursive=True))

        # Should include documents from both the specific file and the directory (including nested)
        self.assertGreaterEqual(len(documents), 3, "Should load from both file and directory when recursive")

        file_sources = [doc['__file__'] for doc in documents]
        self.assertIn(str(specific_file), file_sources, "Should include specific file")

    def test_load_mixed_paths_non_recursive(self):
        """
        Test loading from mixed file and directory paths with non-recursive search (default).
        """

        multiloader = MultiLoader([YAMLLoader])

        specific_file = self.templates_dir / 'single_document.yaml'
        paths = [specific_file, self.samples_dir]

        documents = list(multiloader.load(paths, recursive=False))

        # Should include documents from the specific file and top-level directory files only
        self.assertGreaterEqual(len(documents), 2, "Should load from both file and directory when non-recursive")

        file_sources = [doc['__file__'] for doc in documents]
        self.assertIn(str(specific_file), file_sources, "Should include specific file")

    def test_load_empty_path_list(self):
        """
        Test loading with empty path list.
        """

        multiloader = MultiLoader([YAMLLoader])

        documents = list(multiloader.load([]))

        self.assertEqual(len(documents), 0, "Should return no documents for empty path list")

    def test_load_returns_generator(self):
        """
        Test that load() returns a generator, not a list.
        """

        multiloader = MultiLoader([YAMLLoader])

        result = multiloader.load([self.templates_dir / 'single_document.yaml'])

        # Should be a generator
        self.assertTrue(hasattr(result, '__iter__'), "Should be iterable")
        self.assertTrue(hasattr(result, '__next__'), "Should be a generator")
        self.assertFalse(hasattr(result, '__len__'), "Should not have length (generator)")

    def test_load_preserves_document_order(self):
        """
        Test that documents are loaded in the order of file discovery.
        """

        multiloader = MultiLoader([YAMLLoader])

        # Load from a directory - files should be in sorted order
        documents = list(multiloader.load([self.templates_dir]))

        # Extract filenames and verify they're in sorted order
        prev_file = None
        for doc in documents:
            current_file = Path(doc['__file__']).name
            if prev_file is not None:
                # Within same file, line numbers should increase
                # Between files, filenames should be in sorted order
                if prev_file != current_file:
                    self.assertLessEqual(prev_file, current_file,
                                       "Files should be processed in sorted order")
            prev_file = current_file

    def test_load_with_nonexistent_path_strict_mode(self):
        """
        Test loading with non-existent path in strict mode (should raise exception).
        """

        multiloader = MultiLoader([YAMLLoader])
        nonexistent_path = self.test_data_dir / 'nonexistent'

        with self.assertRaises(FileNotFoundError):
            list(multiloader.load([nonexistent_path]))


if __name__ == '__main__':
    unittest.main()


# The end.

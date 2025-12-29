"""
koji_habitude.loader

YAML file loading, path discovery, and pretty-printing.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: Pure Human


import sys
from itertools import chain
from pathlib import Path
from typing import (
    Any, Dict, Iterable, Iterator, List, Optional, Protocol,
    Sequence, TextIO, Type, Union,
)

from yaml import dump, load_all as _load_all, YAMLError as PyYAMLError
try:
    from yaml import CSafeLoader as SafeLoader, CDumper as Dumper
except ImportError:
    from yaml import SafeLoader, Dumper  # type: ignore

from .exceptions import YAMLError
from .intern import intern
import logging

__all__ = (
    'MultiLoader',
    'YAMLLoader',
    'combine_find_files',
    'find_files',
    'load_all',
    'load_yaml_files',
    'pretty_yaml',
    'pretty_yaml_all',
)


logger = logging.getLogger(__name__)


# this is mostly for testing purposes, but it can be overridden by the user if
# they hate saving memory
ENABLE_INTERNING = True


def load_all(fd: TextIO) -> Iterator[Dict[str, Any]]:
    """
    Load all YAML documents from the given file descriptor.

    :param fd: The file descriptor to load from
    :returns: Iterator of YAML documents
    """
    for doc in _load_all(fd, Loader=MagicSafeLoader):
        yield doc


def load_yaml_files(
        paths: List[Union[str, Path]],
        recursive: bool = False) -> List[Dict[str, Any]]:
    """
    Load YAML file content from the given paths, in order, and return the
    resulting documents as a list.

    A shortcut for creating a :class:`MultiLoader` with the
    :class:`YAMLLoader` class and using it to load the given paths.

    :param paths: List of file paths to load
    :param recursive: Whether to recursively search directories
    :returns: List of YAML documents
    """

    return list(MultiLoader([YAMLLoader]).load(paths, recursive=recursive))


class PrettyYAML(Dumper):
    """
    Custom YAML dumper for pretty-printing.

    It's not as easy as making JSON pretty, but at least it's
    possible.
    """

    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)

    def represent_scalar(self, tag, value, style=None):
        if isinstance(value, str) and '\n' in value:
            # For multi-line strings, use the literal block style ('|')
            return super().represent_scalar(tag, value, style='|')
        else:
            return super().represent_scalar(tag, value, style='')


def pretty_yaml_all(
        sequence: Iterable[Dict[str, Any]],
        out=sys.stdout,
        comments=True,
        **opts) -> None:
    """
    Pretty-print a sequence of YAML documents to the given output stream, with
    document separators.

    Uses :func:`pretty_yaml` to pretty-print each document, and so handles the
    special features of the koji-habitude YAML format, in particular the
    `__file__`, `__line__`, and `__trace__` keys.

    :param sequence: The sequence of YAML documents to pretty-print
    :param out: The output stream to write to
    :param comments: Whether to include comments
    :param opts: Additional options to pass to the yaml.dump function
    """

    for doc in sequence:
        out.write('---\n')
        pretty_yaml(doc, out, comments=comments, **opts)
        out.write('\n')


def pretty_yaml(
        doc: Dict[str, Any],
        out=sys.stdout,
        comments=True,
        **opts) -> None:
    """
    Pretty-print a single YAML object to the given output stream.

    Handles special features of the koji-habitude YAML format, in particular
    the `__file__`, `__line__`, and `__trace__` keys. These are removed from
    the main document body and represented as comments preceeding the
    document.

    :param doc: The YAML document to pretty-print
    :param out: The output stream to write to
    :param comments: Whether to include comments
    :param opts: Additional options to pass to the yaml.dump function
    """

    # we're going to make modifications, so we'll need to make a copy
    doc = doc.copy()

    filename = doc.pop('__file__', None)
    line = doc.pop('__line__', None)
    trace = doc.pop('__trace__', None)

    if comments and filename:
        if line:
            out.write(f"# From: {filename}:{line}\n")
        else:
            out.write(f"# From: {filename}\n")

    if comments and trace:
        out.write('# Trace:\n')
        for tr in trace:
            filename = tr.get('file')
            lineno = tr.get('line')
            template = tr.get('name', '<unknown>')
            if filename:
                if lineno:
                    out.write(f"#   {template} in {filename}:{lineno}\n")
                else:
                    out.write(f"#   {template} in {filename}\n")

    params = {
        'default_flow_style': False,
        'sort_keys': False,
        'explicit_start': False,
    }
    params.update(opts)
    dump(doc, Dumper=PrettyYAML, stream=out, **params)  # type: ignore


class MagicSafeLoader(SafeLoader):
    """
    A SafeLoader with slightly tweaked behavior.

    * adds a ``__line__`` key to each document, representing the line number
      in the file that the document started on.
    """

    def construct_mapping(self, node):
        # Clever and simple trick borrowed from augurar, tweaked to only
        # decorate the documents, not every dict
        # * https://stackoverflow.com/questions/13319067/parsing-yaml-return-with-line-number
        mapping = super().construct_mapping(node)
        mapping['__line__'] = node.start_mark.line + 1
        return mapping


class LoaderProtocol(Protocol):
    extensions: Sequence[str]

    def __init__(self, filename: Union[str, Path]):
        ...

    def load(self) -> Iterator[Dict[str, Any]]:
        ...


class YAMLLoader(LoaderProtocol):
    """
    Wraps the invocation of ``yaml.load_all`` using a customized
    :class:`MagicSafeLoader`, enabling the injection of a ``'__file__'`` and
    ``'__line__'`` key into each doc on load, representing the file path
    it was loaded from, and the line number in that file that the
    document started on.

    Can be added to a :class:`MultiLoader` to enable handling of files with
    .yml and .yaml extensions
    """

    extensions = (".yml", ".yaml")


    def __init__(self, filename: Union[str, Path]):
        """
        Initialize the YAML loader.

        :param filename: The file path to load from
        :raises ValueError: If the filename is not a file
        """

        filename = filename and Path(filename)
        if not (filename and filename.is_file()):
            raise ValueError("filename must be a file")

        self.filename = str(filename)


    def load(self):
        """
        Load YAML documents from the file.

        :returns: Iterator of YAML documents with __file__ and __line__ keys
        :raises YAMLError: If YAML parsing fails
        """

        interning = ENABLE_INTERNING

        with open(self.filename, 'r') as fd:
            logger.debug(f"Loading YAML file {self.filename}")
            try:
                for doc in load_all(fd):
                    doc['__file__'] = self.filename
                    logger.debug(f"Loaded YAML document {self.filename}:{doc['__line__']}")
                    yield intern(doc) if interning else doc

            except PyYAMLError as e:
                raise YAMLError(e, filename=self.filename) from e


class MultiLoader:
    """
    While a :class:`YAMLLoader` can load one file, a MultiLoader can be
    used to load a wide range of files and yield the resulting
    documents in a predictable order
    """

    def __init__(self, loader_types: List[Type[LoaderProtocol]]):
        """
        Initialize the multi-loader.

        :param loader_types: List of loader type classes to register
        """
        self.extmap: Dict[str, Type[LoaderProtocol]] = {}

        for loader in loader_types:
            self.add_loader_type(loader)


    def add_loader_type(
            self,
            loader_type: Type[LoaderProtocol]) -> None:
        """
        Add a loader type to the multi-loader.

        :param loader_type: The loader type class to add
        """

        for ext in loader_type.extensions:
            self.extmap[ext] = loader_type


    def lookup_loader_type(
            self,
            filename: Union[str, Path]) -> Optional[Type[LoaderProtocol]]:
        """
        Lookup the loader type for the given filename.

        :param filename: The filename to lookup the loader type for
        :returns: The loader type for the given filename, or None if not found
        """

        filename = filename and Path(filename)
        if not filename:
            return None
        return self.extmap.get(filename.suffix)


    def loader(self, filename: Union[str, Path]) -> LoaderProtocol:
        """
        Lookup the loader type for the given filename and create an instance of it.

        :param filename: The filename to lookup the loader type for
        :returns: An instance of the loader type for the given filename
        :raises ValueError: If no loader type is found for the given filename
        """

        cls = self.lookup_loader_type(filename)
        if not cls:
            raise ValueError(f"No loader accepting filename {filename}")
        return cls(filename)


    def load(
            self,
            paths: List[Union[str, Path]],
            recursive: bool = False) -> Iterator[Dict[str, Any]]:
        """
        Load YAML documents from the given paths.

        :param paths: List of paths to load from
        :param recursive: Whether to recursively search directories
        :returns: Iterator of YAML documents
        """

        # the extmap is just going to be used to loop over, and to
        # check whether a file suffix is 'in' it, both behaviours are
        # suppoted by dict, so don't bother converting via .keys()
        filepaths = combine_find_files(paths, self.extmap, recursive=recursive, strict=True)
        return chain(*(self.loader(f).load() for f in filepaths))


def find_files(
        pathname: Union[str, Path],
        extensions: Iterable[str] = (".yml", ".yaml"),
        recursive: bool = False,
        strict: bool = True) -> List[Path]:
    """
    Find files with the specified extensions in the given path.

    :param pathname: The path to search
    :param extensions: File extensions to search for
    :param recursive: Whether to recursively search subdirectories
    :param strict: Whether to raise an error if the path doesn't exist
    :returns: List of matching file paths
    :raises ValueError: If pathname is required but not provided
    :raises FileNotFoundError: If strict is True and path doesn't exist
    """

    if not pathname:
        raise ValueError("pathname is required")

    path = pathname if isinstance(pathname, Path) else Path(pathname)

    if strict and not (path and path.exists()):
        raise FileNotFoundError(f"Path not found: {path}")

    if path and path.is_file() and path.suffix in extensions:
        return [path]

    pglob = path.rglob if recursive else path.glob

    found: List[Path] = []
    for ext in extensions:
        found.extend(pglob(f"*{ext}"))

    return sorted(found)


def combine_find_files(
        pathlist: Iterable[Union[str, Path]],
        extensions: Iterable[str] = (".yml", ".yaml"),
        recursive: bool = False,
        strict: bool = True) -> List[Path]:
    """
    Find files in multiple paths using :func:`find_files`.

    :param pathlist: List of paths to search
    :param extensions: File extensions to search for
    :param recursive: Whether to recursively search subdirectories
    :param strict: Whether to raise an error if paths don't exist
    :returns: List of matching file paths
    """

    found: List[Path] = []
    for path in pathlist:
        found.extend(find_files(path, extensions, recursive=recursive, strict=strict))
    return found


# The end.

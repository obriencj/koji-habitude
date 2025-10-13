"""
koji_habitude.loader

YAML file loading, path discovery, and pretty-printing.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: Pure Human


import sys
import yaml

from itertools import chain
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Protocol, Sequence, Type

from .exceptions import YAMLError


__all__ = (
    'MultiLoader',
    'YAMLLoader',
    'combine_find_files',
    'find_files',
    'load_yaml_files',
    'pretty_yaml',
    'pretty_yaml_all',
)


def load_yaml_files(paths: List[str | Path]) -> List[Dict[str, Any]]:
    """
    Load YAML file content from the given paths, in order, and return the
    resulting documents as a list.

    A shortcut for creating a MultiLoader with the YAMLLoader class and
    using it to load the given paths.
    """

    return list(MultiLoader([YAMLLoader]).load(paths))


class PrettyYAML(yaml.Dumper):
    # it's not as easy as making JSON pretty, but at least it's
    # possible.

    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)

    def represent_scalar(self, tag, value, style=None):
        if isinstance(value, str) and '\n' in value:
            # For multi-line strings, use the literal block style ('|')
            return super().represent_scalar(tag, value, style='|')
        else:
            return super().represent_scalar(tag, value, style='')


def pretty_yaml_all(sequence: Iterable[Dict[str, Any]], out=sys.stdout, **opts):
    """
    Pretty-print a sequence of YAML documents to the given output stream, with
    document separators.

    Uses pretty_yaml to pretty-print each document, and so handles the
    special features of the koji-habitude YAML format, in particular the
    __file__, __line__, and __trace__ keys.
    """

    for doc in sequence:
        out.write('---\n')
        pretty_yaml(doc, out, **opts)
        out.write('\n')


def pretty_yaml(doc: Dict[str, Any], out=sys.stdout, **opts):
    """
    Pretty-print a single YAML object to the given output stream.

    Handles special features of the koji-habitude YAML format, in particular the
    __file__, __line__, and __trace__ keys. These are removed from the main
    document body and represented as comments preceeding the document.

    Args:
        doc: The YAML document to pretty-print out: The output stream to write
        to opts: Additional options to pass to the yaml.dump function
    """

    # we're going to make modifications, so we'll need to make a copy
    doc = doc.copy()

    filename = doc.pop('__file__', None)
    line = doc.pop('__line__', None)

    if filename:
        if line:
            out.write(f"# From: {filename}:{line}\n")
        else:
            out.write(f"# From: {filename}\n")

    trace = doc.pop('__trace__', None)
    if trace:
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
    return yaml.dump(doc, Dumper=PrettyYAML, stream=out, **params)  # type: ignore


class MagicSafeLoader(yaml.SafeLoader):
    """
    A SafeLoader with slightly tweaked behavior.

    * allows our anchors to persist across documents
    * adds a __line__ key to each document, representing the line number in the
      file that the document started on.
    """

    def compose_document(self):
        # Allowing our anchors to persist across documents
        self.get_event()
        node = self.compose_node(None, None)
        self.get_event()

        # the default impl resets self.anchors here
        # self.anchors = {}
        return node

    def construct_document(self, node):
        # Clever and simple trick borrowed from augurar, tweaked to only
        # decorate the documents, not every dict
        # * https://stackoverflow.com/questions/13319067/parsing-yaml-return-with-line-number
        mapping = super().construct_document(node)
        mapping['__line__'] = node.start_mark.line + 1
        return mapping


class LoaderProtocol(Protocol):
    extensions: Sequence[str]

    def __init__(self, filename: str | Path):
        ...

    def load(self) -> Iterator[Dict[str, Any]]:
        ...


class YAMLLoader(LoaderProtocol):
    """
    Wraps the invocation of `yaml.load_all` using a customized
    `SafeLoader`, enabling the injection of a `'__file__'` and
    `'__line__'` key into each doc on load, representing the file path
    it was loaded from, and the line number in that file that the
    document started on.

    Can be added to a MultiLoader to enable handling of files with
    .yml and .yaml extensions
    """

    extensions = (".yml", ".yaml")


    def __init__(self, filename: str | Path):

        filename = filename and Path(filename)
        if not (filename and filename.is_file()):
            raise ValueError("filename must be a file")

        self.filename = str(filename)


    def load(self):
        with open(self.filename, 'r') as fd:
            try:
                for doc in yaml.load_all(fd, Loader=MagicSafeLoader):
                    doc['__file__'] = self.filename
                    yield doc
            except yaml.YAMLError as e:
                raise YAMLError(e, filename=self.filename) from e


class MultiLoader:
    """
    While a YAMLLoader can load one file, a MultiLoader can be
    used to load a wide range of files and yield the resulting
    documents in a predictable order
    """

    def __init__(self, loader_types: List[Type[LoaderProtocol]]):
        self.extmap: Dict[str, Type[LoaderProtocol]] = {}

        for loader in loader_types:
            self.add_loader_type(loader)


    def add_loader_type(
            self,
            loader_type: Type[LoaderProtocol]) -> None:

        for ext in loader_type.extensions:
            self.extmap[ext] = loader_type


    def lookup_loader_type(
            self,
            filename: str | Path) -> Type[LoaderProtocol] | None:

        filename = filename and Path(filename)
        if not filename:
            return None
        return self.extmap.get(filename.suffix)


    def loader(self, filename: str | Path) -> LoaderProtocol:
        """
        Lookup the loader type for the given filename and create an instance of it

        Args:
            filename: The filename to lookup the loader type for

        Returns:
            The loader type for the given filename

        Raises:
            ValueError: If no loader type is found for the given filename
        """

        cls = self.lookup_loader_type(filename)
        if not cls:
            raise ValueError(f"No loader accepting filename {filename}")
        return cls(filename)


    def load(self, paths: List[str | Path]) -> Iterator[Dict[str, Any]]:

        # the extmap is just going to be used to loop over, and to
        # check whether a file suffix is 'in' it, both behaviours are
        # suppoted by dict, so don't bother converting via .keys()
        filepaths = combine_find_files(paths, self.extmap, strict=True)
        return chain(*(self.loader(f).load() for f in filepaths))


def find_files(
        pathname: str | Path,
        extensions: Iterable[str] = (".yml", ".yaml"),
        strict: bool = True) -> List[Path]:

    if not pathname:
        raise ValueError("pathname is required")

    path = pathname if isinstance(pathname, Path) else Path(pathname)

    if strict and not (path and path.exists()):
        raise FileNotFoundError(f"Path not found: {path}")

    if path and path.is_file() and path.suffix in extensions:
        return [path]

    found: List[Path] = []
    for ext in extensions:
        found.extend(path.rglob(f"*{ext}"))

    return sorted(found)


def combine_find_files(
        pathlist: Iterable[str | Path],
        extensions: Iterable[str] = (".yml", ".yaml"),
        strict: bool = True) -> List[Path]:

    found: List[Path] = []
    for path in pathlist:
        found.extend(find_files(path, extensions, strict))
    return found


# The end.

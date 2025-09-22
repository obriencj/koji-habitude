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
from typing import Any, Dict, Iterator, List, Protocol, Sequence, Type


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


def pretty_yaml_all(sequence, out=sys.stdout, **opts):
    for doc in sequence:
        pretty_yaml(doc, out, **opts)
        out.write('\n')


def pretty_yaml(doc, out=sys.stdout, **opts):
    doc = doc.copy()
    out.write('---\n')

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
    return yaml.dump(doc, Dumper=PrettyYAML, stream=out, **params)


class NumberedSafeLoader(yaml.SafeLoader):
    # Clever and simple trick borrowed from augurar
    # https://stackoverflow.com/questions/13319067/parsing-yaml-return-with-line-number

    def construct_document(self, node):
        mapping = super().construct_document(node)
        mapping['__line__'] = node.start_mark.line + 1
        return mapping


class LoaderProtocol(Protocol):
    extensions: Sequence[str]
    def __init__(self, filename: str | Path):
        ...
    def load(self) -> Iterator[Dict[str, Any]]:
        ...


class YAMLLoader:

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
            for doc in yaml.load_all(fd, Loader=NumberedSafeLoader):
                doc['__file__'] = self.filename
                yield doc


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
            filename: str | Path) -> Type[LoaderProtocol]:

        filename = filename and Path(filename)
        if not filename:
            return None
        return self.extmap.get(filename.suffix)


    def loader(self, filename: str | Path) -> LoaderProtocol:
        cls = self.lookup_loader_type(filename)
        if not cls:
            raise ValueError(f"No loader accepting filename {filename}")
        return cls(filename)


    def load(self, paths: List[str|Path]) -> Iterator[Dict[str, Any]]:

        # the extmap is just going to be used to loop over, and to
        # check whether a file suffix is 'in' it, both behaviours are
        # suppoted by dict, so don't bother converting via .keys()
        filepaths = combine_find_files(paths, self.extmap)
        return chain(*(self.loader(f).load() for f in filepaths))


def find_files(
        path,
        extensions: Sequence[str] = (".yml", ".yaml"),
        strict: bool = True) -> List[Path]:

    path = path and Path(path)

    if strict and not path.exists():
        raise FileNotFoundError(f"Path not found: {path}")

    if path.is_file() and path.suffix in extensions:
        return [path]

    found = []
    for ext in extensions:
        found.extend(path.rglob(f"*{ext}"))

    return sorted(found)


def combine_find_files(
        pathlist,
        extensions: Sequence[str] = (".yml", ".yaml"),
        strict: bool = True) -> List[Path]:

    found = []
    for path in pathlist:
        found.extend(find_files(path, extensions, strict))
    return found


# The end.

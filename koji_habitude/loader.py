"""
koji_habitude.loader

YAML file loading

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: Pure Human


import yaml

from itertools import chain
from typing import Any, Dict, Iterator, List
from pathlib import Path


class NumberedSafeLoader(yaml.SafeLoader):
    # Clever and simple trick borrowed from augurar
    # https://stackoverflow.com/questions/13319067/parsing-yaml-return-with-line-number

    def construct_mapping(self, node, deep=False):
        mapping = super().construct_mapping(node, deep=deep)
        mapping['__line__'] = node.start_mark.line + 1
        return mapping


def YAMLLoader:

    """
    Wraps the invocation of `yaml.load_all` using a customized `SafeLoader`,
    enabling the injection of a `'__file__'` and `'__line__'` key into each
    doc on load, representing the file path it was loaded from, and the
    line number in that file that the document started on.

    Can be added to a MultiLoader to enable handling of files with
    .yml and .yaml extensions
    """


    extensions = (".yml", ".yaml")


    def __init__(self, filename: str|Path):

        filename = filename and Path(filename)
        if not (filename and filename.is_file()):
            raise ValueError("filename must be a file")

        self.filename = str(filename)


    def load(self):
        with open(self.filename, 'r') as fd:
            for doc in yaml.load_all(fd, Loader=NumberedSafeLoader):
                doc['__file__'] = self.filename
                yield doc


def MultiLoader:

    def __init__(self, loader_types=[]):
        self.extmap = {}

        for loader in loader_types:
            self.add_loader(loader)


    def add_loader_type(self, loader_type):
        for ext in loader_type.extensions:
            self.extmap[ext] = loader_type


    def lookup_loader_type(self, filename: str|Path):
        filename = filename and Path(filename)
        if not filename:
            return None
        return self.extmap.get(filename.suffix)


    def loader(self, filename: str|Path):
        cls = self.lookup_loader_type(filename)
        if not cls:
            raise ValueError("No loader accepting filename {filename}")
        return cls(filename)


    def load(self, filepaths: List[str|Path]) -> Iterator[Dict[str, Any]]:
        """
        loads in-sequence, to ensure a predictably ordered object
        stream. filepaths needs to be a list of files. If you're working
        with a mixture of directories, use `loader.combine_find_files`
        to flatten dirs and file into an orderly list as expected by
        this method.
        """

        return chain(*(loader(f).load() for f in filepaths))


def find_files(path, extensions=(".yml", ".yaml")):
    path = path and Path(path)
    if path.is_file() and path.suffix in extensions:
        return [path]

    found = []
    for ext in extensions:
        found.extend(path.rglob(f"*{ext}"))

    return sorted(found)


def combine_find_files(pathlist, extensions=(".yml", ".yaml")):
    found = []
    for path in pathlist:
        found.extend(find_files(path, extentions))
    return found


# The end.

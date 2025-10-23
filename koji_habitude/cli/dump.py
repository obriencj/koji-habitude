"""
koji_habitude.cli.dump

Dump remote data from Koji instance by pattern matching.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 4.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Assisted, Mostly Human


import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

import click

from ..koji import session, multicall
from ..loader import pretty_yaml_all
from ..models import BaseKey
from ..namespace import Namespace
from ..resolver import Reference, Resolver
from . import main
from .util import catchall, sort_objects_for_output


def parse_patterns(args: List[str], default_types: List[str]) -> List[BaseKey]:
    """
    Parse command line arguments into (type, pattern) tuples.

    Args:
        args: List of arguments like ['tag:foo', '*-build', 'user:bob']
        default_types: List of types to use for untyped patterns
    """
    result = []
    for arg in args:
        if ':' in arg:
            type_part, pattern = arg.split(':', 1)
            result.append((type_part, pattern))
        else:
            for typename in default_types:
                result.append((typename, arg))
    return result


def search_tags(session_obj, pattern: str) -> List[BaseKey]:
    """Search for tags using koji search API."""
    return [('tag', v['name']) for v in session_obj.search(pattern, 'tag', 'glob')]


def search_targets(session_obj, pattern: str) -> List[BaseKey]:
    """Search for targets using koji search API."""
    return [('target', v['name']) for v in session_obj.search(pattern, 'target', 'glob')]


def search_users(session_obj, pattern: str) -> List[BaseKey]:
    """Search for users using koji search API."""
    return [('user', v['name']) for v in session_obj.search(pattern, 'user', 'glob')]


def search_hosts(session_obj, pattern: str) -> List[BaseKey]:
    """Search for hosts using koji search API."""
    return [('host', v['name']) for v in session_obj.search(pattern, 'host', 'glob')]


# Registry of search functions
SEARCH_FUNCTIONS = {
    'tag': search_tags,
    'target': search_targets,
    'user': search_users,
    'host': search_hosts,
}


glob_like = re.compile(r'[\*\?\[\]]').search


def resolve_term(session, resolver: Resolver, key: BaseKey) -> List[Reference]:
    typename, name = key

    print(f"Resolving {key}")
    if glob_like(name):
        search_fn = SEARCH_FUNCTIONS.get(typename)
        if search_fn is None:
            raise ValueError(f"No search function for type {typename}")
        print(f"Searching {search_fn!r} for {name!r}")
        return [resolver.resolve(key) for key in search_fn(session, name)]
    else:
        return [resolver.resolve(key)]


@main.command()
@click.argument('patterns', nargs=-1, required=True)
@click.option(
    '--profile', "-p", default='koji',
    help="Koji profile to use for connection")
@click.option(
    "--output", "-o", default=sys.stdout, type=click.File('w'), metavar='PATH',
    help="Path to output YAML file (default: stdout)")
@click.option(
    "--include-defaults", "-d", default=False, is_flag=True,
    help="Whether to include default values (bool default: False)")
@click.option(
    "--with-deps", default=False, is_flag=True,
    help="Include dependencies (default: False)")
@click.option(
    "--dep-depth", type=int, default=None, metavar='N',
    help="Maximum dependency depth (default: unlimited)")
@click.option(
    "--tags", default=False, is_flag=True,
    help="Search tags by default for untyped patterns")
@click.option(
    "--targets", default=False, is_flag=True,
    help="Search targets by default")
@click.option(
    "--users", default=False, is_flag=True,
    help="Search users by default")
@click.option(
    "--hosts", default=False, is_flag=True,
    help="Search hosts by default")
@catchall
def dump(patterns, profile='koji', output=sys.stdout, include_defaults=False,
         with_deps=False, dep_depth=None, tags=False, targets=False,
         users=False, hosts=False):
    """
    Dump remote data from Koji instance by pattern matching.

    Searches koji for objects matching the given patterns and outputs
    their remote state as YAML. Supports both exact matches and pattern
    matching for searchable types (tags, targets, users, hosts).

    PATTERNS can be:
    - TYPE:PATTERN (e.g., 'tag:foo', 'user:*bob*')
    - PATTERN (applied to default types, e.g., '*-build')

    Examples:
    - koji-habitude dump tag:foo *-build
    - koji-habitude dump --tags --users *bob*
    - koji-habitude dump tag:f40-build --with-deps --dep-depth 2
    """

    # Determine default types from flags
    default_types = []
    if tags:
        default_types.append('tag')
    if targets:
        default_types.append('target')
    if users:
        default_types.append('user')
    if hosts:
        default_types.append('host')

    # Default to tags and targets if no flags specified
    if not default_types:
        default_types = ['tag', 'target']

    # Parse patterns
    search_list = parse_patterns(patterns, default_types)

    # Connect to koji (no auth, read-only)
    session_obj = session(profile, authenticate=False)

    # we'll use a Resolver to create Reference objects to use in lookups
    resolver = Resolver(Namespace())

    # performs searches and resolves individual units to References
    for key in search_list:
        refs = resolve_term(session, resolver, key)
        for ref in refs:
            print(f"Resolved {ref!r}")

    resolver.load_remote_references(session_obj, full=True)

    # Resolve dependencies if requested
    # if with_deps:
    #     resolve_dependencies(session_obj, resolver, dep_depth)

    remotes = [ref.remote() for ref in resolver.report().discovered.values()]
    sorted_objects = sort_objects_for_output(remotes)

    # Convert to dicts and output YAML
    exclude_defaults = not include_defaults
    series = (obj.to_dict(exclude_defaults=exclude_defaults) for obj in sorted_objects)
    pretty_yaml_all(series, out=output)

    return 0


# The end.

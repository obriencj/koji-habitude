"""
koji_habitude.cli.dump

Dump remote data from Koji instance by pattern matching.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 4.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Assisted, Mostly Human


import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

import click

from ..koji import session
from ..loader import pretty_yaml_all
from ..models import CORE_MODELS, BaseKey
from ..namespace import Namespace
from ..resolver import Reference, Resolver
from . import main
from .util import catchall, sort_objects_for_output, resplit


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
    return [('tag', v['name']) for v in session_obj.search(pattern, 'tag', 'glob')]


def search_targets(session_obj, pattern: str) -> List[BaseKey]:
    return [('target', v['name']) for v in session_obj.search(pattern, 'target', 'glob')]


def search_users(session_obj, pattern: str) -> List[BaseKey]:
    return [('user', v['name']) for v in session_obj.search(pattern, 'user', 'glob')]


def search_hosts(session_obj, pattern: str) -> List[BaseKey]:
    return [('host', v['name']) for v in session_obj.search(pattern, 'host', 'glob')]


# Registry of search functions
SEARCH_FUNCTIONS = {
    'tag': search_tags,
    'target': search_targets,
    'user': search_users,
    'host': search_hosts,
}


glob_like = re.compile(r'[\*\?\[\]]').search


def resolve_term(session_obj, resolver: Resolver, key: BaseKey):
    typename, name = key

    if glob_like(name):
        search_fn = SEARCH_FUNCTIONS.get(typename)
        if search_fn is None:
            raise ValueError(f"No search function for type in key, {key}")
        return [resolver.resolve(key) for key in search_fn(session_obj, name)]
    else:
        return [resolver.resolve(key)]


def resolve_dependencies(
        session_obj,
        resolver: Resolver,
        max_depth: Optional[int] = None,
        dep_types: Optional[List[str]] = None) -> None:

    work = list(resolver.report().discovered.values())
    while work:
        new_work = []
        for ref in work:
            remote = ref.remote()
            assert remote is not None

            for depkey in remote.dependency_keys():
                if dep_types and depkey[0] not in dep_types:
                    continue
                depref = resolver.resolve(depkey)
                if depref.remote() is None:
                    new_work.append(depref)

        work = new_work
        if not work:
            break

        resolver.load_remote_references(session_obj, full=True)
        if max_depth is not None:
            if max_depth <= 1:
                break
            max_depth -= 1


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
    "--with-dep-type", multiple=True, metavar='TYPE',
    help="Limit dependencies to specific types (default: None)")
@click.option(
    "--max-depth", type=int, default=None, metavar='N',
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
def dump(patterns, profile='koji', output=sys.stdout,
         include_defaults=False, with_deps=False, with_dep_type=[],
         max_depth=None, tags=False, targets=False,
         users=False, hosts=False):
    """
    Dump remote data from Koji instance by pattern matching.

    Searches koji for objects matching the given patterns and outputs
    their remote state as YAML. Supports both exact matches and pattern
    matching for searchable types (tags, targets, users, hosts).

    \b
    PATTERNS can be:
      - TYPE:PATTERN (e.g., 'tag:foo', 'user:*bob*')
      - PATTERN (applied to default types, e.g., '*-build')

    \b
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

    if with_dep_type:
        with_deps = True
        with_dep_type = resplit(with_dep_type)
        for dep_type in with_dep_type:
            if dep_type not in SEARCH_FUNCTIONS:
                click.echo(f"Invalid dependency type: {dep_type}", err=True)
                return 1

    # Parse patterns
    search_list = parse_patterns(patterns, default_types)
    for key in search_list:
        if key[0] not in CORE_MODELS:
            click.echo(f"Invalid type in key: {key}", err=True)
            return 1

    # Connect to koji (no auth, read-only)
    session_obj = session(profile, authenticate=False)

    # we'll use a Resolver to create Reference objects to use in lookups
    resolver = Resolver(Namespace())

    # performs searches and resolves individual units to References
    try:
        for key in search_list:
            resolve_term(session_obj, resolver, key)
    except ValueError as e:
        click.echo(e.message, err=True)
        return 1

    resolver.load_remote_references(session_obj, full=True)

    # Resolve dependencies if requested
    if with_deps:
        resolve_dependencies(session_obj, resolver, max_depth, with_dep_type)

    remotes = [ref.remote() for ref in resolver.report().discovered.values()]
    sorted_objects = sort_objects_for_output(remotes)

    # Convert to dicts and output YAML
    exclude_defaults = not include_defaults
    series = (obj.to_dict(exclude_defaults=exclude_defaults) for obj in sorted_objects)
    pretty_yaml_all(series, out=output)

    return 0


# The end.

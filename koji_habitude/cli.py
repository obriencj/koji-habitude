"""
koji_habitude.cli

Main CLI interface using clique with orchestration of the
synchronization process.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

import sys
from pathlib import Path
from typing import Optional, List, Tuple

import clique

from .loader import MultiLoader
from .namespace import Namespace, TemplateNamespace


def resplit(strs: List[str], sep=',') -> List[str]:
    return list(filter(map(str.strip, sep.join(strs).split(sep))))


@clique.command()
@clique.option(
    '--templates', metavar='PATH', nargs=-1,
    help="Location to find templates that are not available in DATA")
@clique.option(
    '--profile',
    help="Koji profile to use for connection")
@clique.option(
    '--offline', is_flag=True,
    help="Run in offline mode (no koji connection)")
@clique.option(
    '--dry-run', is_flag=True,
    help="Show what would be done without making changes")
@clique.argument('data', nargs=-1, required=True, metavar='DATA')
def sync(
        templates: List[str],
        profile: Optional[str],
        offline: bool,
        dry_run: bool,
        data: List[str]):

    # TODO
    pass


@clique.command()
@clique.option(
    '--templates', metavar='PATH',
    help="Location to find templates that are not available in DATA")
@clique.option(
    '--profile',
    help="Koji profile to use for connection")
@clique.option(
    '--offline', is_flag=True,
    help="Run in offline mode (no koji connection)")
@clique.argument('data', nargs=-1, required=True, metavar='DATA')
def diff(
        templates: Optional[str],
        profile: Optional[str],
        offline: bool,
        data: Tuple[str, ...]):

    """
    Show what changes would be made without applying them.

    This is a convenience alias for 'sync --dry-run'.

    DATA can be directories or files containing YAML object definitions.
    """

    # Call sync with dry_run=True
    return sync(templates, profile, offline, True, data)


@clique.command()
@clique.argument('paths', nargs=-1, required=True, metavar='PATH')
def list_templates(paths: Tuple[str, ...]):
    """
    List available templates.

    Shows all templates found in the given locations with their
    configuration details.

    PATH can be directories containing template files.
    """

    ns = TemplateNamespace()
    ml = MultiLoader()
    ns.feedall_raw(ml.load(paths))

    for name, templ in ns.templates.items():
        print(f"{name} from ")


@clique.command()
@clique.option('--templates', metavar='PATH', help="Location to find templates that are not available in DATA")
@clique.argument('data', nargs=-1, required=True, metavar='DATA')
def validate(templates: Optional[str], data: Tuple[str, ...]):
    """
    Validate data files and templates.

    Loads and validates all templates and data files without connecting to koji.

    DATA can be directories or files containing YAML object definitions.
    """

    pass


@clique.group()
def main():
    """
    koji-habitude - Synchronize local koji data expectations with hub instance.

    This tool loads YAML templates and data files, resolves dependencies,
    and applies changes to a koji hub in the correct order.
    """

    pass


# Register subcommands
main.add_command(sync)
main.add_command(diff)
main.add_command(list_templates)
main.add_command(validate)


if __name__ == '__main__':
    sys.exit(main())


# The end.

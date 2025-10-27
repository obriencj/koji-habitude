"""
koji_habitude.cli.fetch

Fetch remote data from Koji instance and output as YAML.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 4.5 Sonnet via Cursor
"""


import sys

import click

from ..loader import pretty_yaml_all
from ..resolver import Reference
from ..workflow import CompareWorkflow
from . import main
from .util import catchall, sort_objects_for_output


@main.command()
@click.argument('data', nargs=-1, required=True)
@click.option(
    '--templates', "-t", metavar='PATH', multiple=True,
    help="Location to find templates that are not available in DATA")
@click.option(
    '--recursive', '-r', is_flag=True, default=False,
    help="Search template and data directories recursively")
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
    "--show-unchanged", "-u", default=False, is_flag=True,
    help="Whether to show unchanged objects (bool default: False)")
@catchall
def fetch(data, templates, recursive=False,
          profile='koji', output=sys.stdout,
          include_defaults=False, show_unchanged=False):
    """
    Fetch remote data from Koji instance and output as YAML.

    Loads templates and data files, resolves dependencies, connects to
    Koji, and outputs YAML documents representing the remote state of
    all objects that exist on the Koji instance which have fields that
    differ from the local definitions.

    The `--show-unchanged` option will show all objects from the dataseries,
    regardless of whether they differ.

    DATA can be directories or files containing YAML object definitions.
    """

    workflow = CompareWorkflow(
        paths=data,
        template_paths=templates,
        recursive=recursive,
        profile=profile)
    workflow.run()

    exclude_defaults = not include_defaults

    if show_unchanged:
        # just show all objects from the dataseries
        work_objects = workflow.dataseries
    else:
        work_objects = []
        for change_report in workflow.summary.change_reports.values():
            if len(change_report.changes):
                work_objects.append(change_report.obj)

    remote_objects = []
    for obj in work_objects:
        if isinstance(obj, Reference):
            continue

        remote = obj.remote()
        if remote is None:
            continue

        remote_objects.append(remote)

    # Sort objects by type, then by name
    sorted_objects = sort_objects_for_output(remote_objects)

    # Output all remote objects as YAML
    series = (remote.to_dict(exclude_defaults=exclude_defaults) for remote in sorted_objects)
    pretty_yaml_all(series, out=output)

    return 0


# The end.

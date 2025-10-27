"""
koji_habitude.cli.diff

Show unified diff between local and remote YAML objects.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 4.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Assisted, Mostly Human


import click

from ..workflow import CompareWorkflow
from . import main
from .util import catchall, display_summary_as_diff


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
    "--include-defaults", "-d", default=False, is_flag=True,
    help="Whether to include default values (bool default: False)")
@click.option(
    "--context", "-c", default=3, type=int, metavar='N',
    help="Number of context lines around each change (default: 3)")
@catchall
def diff(data, templates, recursive=False,
         profile='koji', include_defaults=False, context=3):
    """
    Show unified diff between local and remote YAML objects.

    Compares local definitions against remote koji state and displays
    a unified diff for objects that differ.

    DATA can be directories or files containing YAML object definitions.
    """

    workflow = CompareWorkflow(
        paths=data,
        template_paths=templates,
        recursive=recursive,
        profile=profile)
    workflow.run()

    exclude_defaults = not include_defaults
    diffcount = display_summary_as_diff(
        workflow.summary,
        context=context,
        exclude_defaults=exclude_defaults)

    return 0 if not diffcount else 1


# The end.

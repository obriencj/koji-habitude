"""
koji_habitude.cli.compare

Compare local data against a Koji instance

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 3.5 Sonnet via Cursor
"""


import click

from . import main
from ..workflow import CompareWorkflow
from .util import catchall, display_resolver_report, display_summary


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
    '--show-unchanged', 'show_unchanged', is_flag=True, default=False,
    help="Show objects that don't need any changes")
@catchall
def compare(data, templates=None, recursive=False,
            profile='koji', show_unchanged=False):
    """
    Show what changes would be made without applying them.

    DATA can be directories or files containing YAML object
    definitions.
    """

    workflow = CompareWorkflow(
        paths=data,
        template_paths=templates,
        recursive=recursive,
        profile=profile)
    workflow.run()

    display_summary(workflow.summary, show_unchanged)
    display_resolver_report(workflow.resolver_report)

    return 1 if workflow.resolver_report.phantoms else 0


# The end.

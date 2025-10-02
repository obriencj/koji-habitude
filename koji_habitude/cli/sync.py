"""
koji_habitude.cli.sync

Synchronize with Koji hub.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""


import click

from . import main
from ..workflow import SyncWorkflow as _SyncWorkflow
from ..workflow import WorkflowMissingObjectsError
from .diff import catchall, display_missing, display_summary


class SyncWorkflow(_SyncWorkflow):

    def processor_step_callback(self, step, handled):
        click.echo(f"Step #{step} processed chunk of {handled} objects")
        report = self.resolver.report()
        if report.missing:
            for key in report.missing:
                click.echo(f"Dependency missing: {key[0]} {key[1]}")
            msg = "Missing dependencies found in the system"
            raise click.ClickException(msg)


@main.command()
@click.argument('data', nargs=-1, required=True)
@click.option(
    '--templates', metavar='PATH', multiple=True,
    help="Location to find templates that are not available in DATA")
@click.option(
    '--profile', default='koji',
    help="Koji profile to use for connection")
@click.option(
    '--show-unchanged', 'show_unchanged', is_flag=True, default=False,
    help="Show objects that don't need any changes")
@catchall
def sync(data, templates=None, profile='koji', show_unchanged=False):
    """
    Synchronize local koji data expectations with hub instance.

    Loads templates and data files, resolves dependencies, and applies
    changes to the koji hub in the correct order.

    DATA can be directories or files containing YAML object
    definitions.
    """

    try:
        workflow = SyncWorkflow(data, templates, profile)
        workflow.run()
    except WorkflowMissingObjectsError as e:
        display_missing(e.report)
        return 1

    display_summary(workflow.summary, show_unchanged)
    display_missing(workflow.missing_report)

    return 0


# The end.

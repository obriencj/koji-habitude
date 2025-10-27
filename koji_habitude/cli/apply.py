"""
koji_habitude.cli.apply

Apply data onto a Koji hub instance.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 3.5 Sonnet via Cursor
"""


import click

from . import main
from ..workflow import ApplyWorkflow as _ApplyWorkflow
from ..workflow import WorkflowPhantomsError
from .util import catchall, display_resolver_report, display_summary


class ApplyWorkflow(_ApplyWorkflow):

    def workflow_state_change(self, from_state, to_state) -> bool:
        return False

    def processor_step_callback(self, step, handled) -> None:
        pass


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
@click.option(
    '--skip-phantoms', 'skip_phantoms', is_flag=True, default=False,
    help="Skip objects that have phantom dependencies")
@catchall
def apply(data, templates=None, recursive=False,
          profile='koji',
          show_unchanged=False, skip_phantoms=False):
    """
    Apply local koji data expectations onto the hub instance.

    Loads templates and data files, resolves dependencies, and applies
    changes to the koji hub in the correct order.

    DATA can be directories or files containing YAML object
    definitions.
    """

    workflow = ApplyWorkflow(
        paths=data,
        template_paths=templates,
        recursive=recursive,
        profile=profile,
        skip_phantoms=skip_phantoms)

    try:
        workflow.run()
    except WorkflowPhantomsError as e:
        display_resolver_report(e.report)
        return 1
    else:
        display_summary(workflow.summary, show_unchanged)
        display_resolver_report(workflow.resolver_report)
        return 0


# The end.

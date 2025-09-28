"""
koji_habitude.cli.sync

Synchronize with Koji hub.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""


import click

from ..workflow import SyncWorkflow as _SyncWorkflow
from ..workflow import WorkflowMissingObjectsError

from . import main, catchall


class SyncWorkflow(_SyncWorkflow):

    def processor_step_callback(self, step, handled):
        click.echo(f"Step #{step} processed chunk of {handled} objects")
        report = self.resolver.report()
        if report.missing:
            for key in report.missing:
                click.echo(f"Dependency missing: {key[0]} {key[1]}")
            raise click.ClickException("Missing dependencies found in the system")


def display_summary(summary, report, show_unchanged):
    """
    Display the summary of the changes with proper grouping and indentation.
    """

    # Group change reports by object type
    by_type = {}
    unchanged_objects = []

    for key, change_report in summary.change_reports.items():
        typename, name = key
        if len(change_report.changes) == 0:
            unchanged_objects.append((typename, name))
        else:
            if typename not in by_type:
                by_type[typename] = []
            by_type[typename].append((name, change_report))

    # Display objects with changes
    if by_type:
        click.echo("Objects with changes:")
        click.echo()

        for typename in sorted(by_type.keys()):
            click.echo(f"{typename}:")
            for name, change_report in sorted(by_type[typename]):
                click.echo(f"  {name}:")
                for change in change_report.changes:
                    click.echo(f"    {change.explain()}")
            click.echo()

    # Display unchanged objects if requested
    if show_unchanged and unchanged_objects:
        click.echo("Objects with no changes needed:")
        click.echo()

        by_type_unchanged = {}
        for typename, name in unchanged_objects:
            if typename not in by_type_unchanged:
                by_type_unchanged[typename] = []
            by_type_unchanged[typename].append(name)

        for typename in sorted(by_type_unchanged.keys()):
            click.echo(f"{typename}:")
            for name in sorted(by_type_unchanged[typename]):
                click.echo(f"  {name}")
            click.echo()

    # Summary
    total_changes = summary.total_changes
    total_objects = len(summary.change_reports)
    unchanged_count = len(unchanged_objects)

    if total_changes > 0:
        click.echo(f"Summary: {total_changes} changes across {total_objects - unchanged_count} objects")
    else:
        click.echo("Summary: No changes needed")

    if show_unchanged and unchanged_count > 0:
        click.echo(f"({unchanged_count} objects unchanged)")

    click.echo()


def display_missing(report):
    if report:
        total_dependencies = len(report.found) + len(report.missing)
        click.echo(f"Resolver identified {total_dependencies} dependencies not defined in the data set")
        click.echo(f"({len(report.found)} were found in the system, {len(report.missing)} remain missing)")

    if report.found:
        click.echo("Found objects:")
        for key in report.found:
            click.echo(f"  {key[0]} {key[1]}")

    if report.missing:
        click.echo("Missing objects:")
        for key in report.missing:
            click.echo(f"  {key[0]} {key[1]}")

    click.echo()


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

    Loads templates and data files, resolves dependencies, and applies changes
    to the koji hub in the correct order.

    DATA can be directories or files containing YAML object definitions.
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

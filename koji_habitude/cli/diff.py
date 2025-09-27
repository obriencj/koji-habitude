"""
koji_habitude.cli.diff

Diff two sets of data.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""


import click

from ..loader import MultiLoader, YAMLLoader
from ..namespace import Namespace, TemplateNamespace
from ..resolver import Resolver
from ..solver import Solver
from ..processor import DiffOnlyProcessor
from ..koji import session


def _run_diff(templates, profile, offline, show_unchanged, data):
    """
    Run the diff command to show what changes would be made.
    """
    try:
        # Load templates if provided
        template_ns = TemplateNamespace()
        if templates:
            ml = MultiLoader([YAMLLoader])
            template_ns.feedall_raw(ml.load(templates))
            template_ns.expand()

        # Create regular Namespace with loaded templates
        data_ns = Namespace()
        data_ns._templates.update(template_ns._templates)

        # Load and process data files
        ml = MultiLoader([YAMLLoader])
        data_ns.feedall_raw(ml.load(data))
        data_ns.expand()

        # Create resolver and solver
        resolver = Resolver(data_ns)
        solver = Solver(resolver)
        solver.prepare()

        koji_session = session(profile)

        # Create and run DiffOnlyProcessor
        processor = DiffOnlyProcessor(
            koji_session=koji_session,
            stream_origin=solver,
            chunk_size=100
        )

        processor = DiffOnlyProcessor(
            koji_session=koji_session,
            stream_origin=solver,
            chunk_size=100
        )

        summary = processor.run()

        # Display results
        _display_diff_results(summary, show_unchanged)

        return 0

    except Exception as e:
        import traceback
        click.echo(f"Error: {e}", err=True)
        click.echo(traceback.format_exc(), err=True)
        return 1


def _display_diff_results(summary, show_unchanged):
    """
    Display the diff results with proper grouping and indentation.
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


@click.command()
@click.option(
    '--templates', 'templates', metavar='PATH', multiple=True,
    help="Location to find templates that are not available in DATA")
@click.option(
    '--profile',
    help="Koji profile to use for connection")
@click.option(
    '--offline', 'offline', is_flag=True,
    help="Run in offline mode (no koji connection)")
@click.option(
    '--show-unchanged', 'show_unchanged', is_flag=True, default=False,
    help="Show objects that don't need any changes")
@click.argument('data', nargs=-1, required=True)
def diff(templates, profile, offline, show_unchanged, data):

    """
    Show what changes would be made without applying them.

    This is a convenience alias for 'sync --dry-run'.

    DATA can be directories or files containing YAML object definitions.
    """

    # Call the diff functionality directly
    return _run_diff(templates, profile, offline, show_unchanged, data)


# The end.

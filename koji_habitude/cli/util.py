"""
koji_habitude.cli.util

Utility functions for the CLI.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""


import click
from typing import List
from functools import wraps
from pydantic import ValidationError
from koji import GSSAPIAuthError, GenericError


def resplit(strs: List[str], sep=',') -> List[str]:
    """
    Takes a list of strings which may be comma-separated to indicate multiple
    values. Returns a list of strings with the commas removed and those values
    expanded, whitespace stripped, and any empty strings omitted.

    Example:
        >>> resplit(['foo', ' ', 'bar,baz', 'qux,,quux'])
        ['foo', 'bar', 'baz', 'qux', 'quux']
    """

    # joins 'em, splits 'em, strips 'em, and filters 'em
    return list(filter(None, map(str.strip, sep.join(strs).split(sep))))


def catchall(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        except ValidationError as e:
            click.echo(f"[ValidationError] {e}", err=True)
            return 1

        except GSSAPIAuthError as e:
            click.echo(f"[GSSAPIAuthError] {e}", err=True)
            return 1

        except GenericError as e:
            click.echo(f"[GenericError] {e}", err=True)
            return 1

        except KeyboardInterrupt:
            click.echo("[Keyboard interrupt]", err=True)
            return 130

        except Exception as e:
            click.echo(f"[Error] {e}", err=True)
            raise

    return wrapper


def display_summary(summary, show_unchanged):
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


# The end.
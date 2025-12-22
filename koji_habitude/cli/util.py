"""
koji_habitude.cli.util

Utility functions for the CLI.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 4.5 Sonnet via Cursor
"""


from difflib import unified_diff
from functools import wraps
from io import StringIO
from typing import List

from click import echo
from koji import GenericError, GSSAPIAuthError

from ..exceptions import (
    ChangeApplyError, ChangeReadError, ExpansionError,
    HabitudeError, KojiError, RedefineError,
    TemplateError, ValidationError, YAMLError,
)
from ..loader import pretty_yaml
from ..resolver import Reference
from .theme import select_theme

__all__ = (
    'catchall',
    'display_summary',
    'display_resolver_report',
    'resplit',
    'sort_objects_for_output',
)


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
    """
    Decorator that catches and formats exceptions for CLI display.

    HabitudeError exceptions are displayed with their rich context (file location,
    template trace, etc.). Other exceptions are displayed with basic formatting.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        except YAMLError as e:
            # YAML parsing errors - show formatted error with file context
            echo(f"YAML Error:\n{e}", err=True)
            return 1

        except ValidationError as e:
            # Validation errors - show formatted error with object and file context
            echo(f"Validation Error:\n{e}", err=True)
            return 1

        except (TemplateError, ExpansionError) as e:
            # Template errors - show formatted error with template context
            echo(f"Template Error:\n{e}", err=True)
            return 1

        except RedefineError as e:
            # Redefinition errors - show formatted error with object locations
            echo(f"Redefinition Error:\n{e}", err=True)
            return 1

        except KojiError as e:
            # Koji API errors - show formatted error with operation context
            echo(f"Koji Error:\n{e}", err=True)
            return 1

        except GSSAPIAuthError as e:
            # Koji authentication errors (not wrapped by us)
            echo(f"Authentication Error: {e}", err=True)
            return 1

        except GenericError as e:
            # Generic koji errors (not wrapped by us)
            echo(f"Koji Error: {e}", err=True)
            return 1

        except HabitudeError as e:
            # Catch-all for any other HabitudeError subclasses
            echo(f"Error:\n{e}", err=True)
            return 1

        except KeyboardInterrupt:
            echo("\n[Interrupted]", err=True)
            return 130

        except Exception as e:
            # Unexpected errors - display and re-raise for debugging
            echo(f"Unexpected Error: {e}", err=True)
            raise

    return wrapper


def display_summary(summary, show_unchanged, theme=None):
    """
    Display the summary of the changes with proper grouping and indentation.
    """

    if theme is None:
        theme = select_theme()

    style = theme.style
    secho = theme.secho

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
        echo("Objects with changes:")
        echo()

        for typename in sorted(by_type.keys()):
            echo(style(f"{typename}:", tp='type_heading'))
            for name, change_report in sorted(by_type[typename]):
                echo(f"  {style(name, tp='object_name')}:")
                for change in change_report.changes:
                    echo(f"    {style(change.summary(), tp=change.style_name)}")
            echo()

    # Display unchanged objects if requested
    if show_unchanged and unchanged_objects:
        echo("Objects with no changes needed:")
        echo()

        by_type_unchanged = {}
        for typename, name in unchanged_objects:
            if typename not in by_type_unchanged:
                by_type_unchanged[typename] = []
            by_type_unchanged[typename].append(name)

        for typename in sorted(by_type_unchanged.keys()):
            secho(f"{typename}:", tp='type_heading')
            for name in sorted(by_type_unchanged[typename]):
                secho(f"  {name}", tp='unchanged_text')
            echo()

    # Summary
    total_changes = summary.total_changes
    total_objects = len(summary.change_reports)
    unchanged_count = len(unchanged_objects)

    if total_changes > 0:
        summary_msg = (f"Summary: {total_changes} changes across"
                       f" {total_objects - unchanged_count} objects")
        secho(summary_msg, tp='summary_text')
    else:
        secho("Summary: No changes needed", tp='summary_text')

    if show_unchanged and unchanged_count > 0:
        unchanged_msg = f"({unchanged_count} objects unchanged)"
        secho(unchanged_msg, tp='unchanged_text')

    echo()


def display_resolver_report(report, theme=None):
    """
    Display the resolver report with colorization.
    """

    if theme is None:
        theme = select_theme()

    style = theme.style
    secho = theme.secho

    total_dependencies = len(report.discovered) + len(report.phantoms)

    if not total_dependencies:
        return

    main_msg = f"Resolver identified {total_dependencies} dependency references not defined in the data set"
    secho(main_msg, tp='summary_text')

    detail_msg = (f"({len(report.discovered)} were discovered in the system,"
                  f" {len(report.phantoms)} phantoms remain)")
    secho(detail_msg, tp='unchanged_text')

    if report.discovered:
        secho("Discovered references:", tp='type_heading')
        for key in sorted(report.discovered):
            echo(f"  {style(key[0], tp='object_name')} {style(key[1], tp='object_name')}")

    if report.phantoms:
        secho("Phantom references:", tp='type_heading')
        for key in sorted(report.phantoms):
            echo(f"  {style(key[0], tp='object_name')} {style(key[1], tp='object_name')}")

    echo()


def sort_objects_for_output(objects):
    """
    Sort objects for consistent YAML output.

    Groups objects by typename, sorts each group by name,
    and returns flattened list in type-then-name order.

    Args:
        objects: Iterable of objects with .typename and .name attributes

    Returns:
        List of objects sorted by type, then by name
    """

    dedup = {obj.key(): obj for obj in objects}
    return [item[1] for item in sorted(dedup.items())]


def display_summary_as_diff(
        summary,
        context=3,
        exclude_defaults=False,
        theme=None):
    """
    Display the summary of the changes as a unified diff.

    :param summary: The summary of the changes
    :param context: The number of context lines to show
    :param exclude_defaults: Whether to exclude default values
    :param theme: The theme to use for the output

    :returns: None
    """

    if theme is None:
        theme = select_theme()

    secho = theme.secho

    # Only show objects with changes
    work_objects = []
    for change_report in summary.change_reports.values():
        if len(change_report.changes):
            work_objects.append(change_report.obj)

    # Get local and remote objects for diffing
    diff_pairs = []
    for obj in work_objects:
        if isinstance(obj, Reference):
            continue

        remote = obj.remote()
        diff_pairs.append((obj, remote))

    # Sort objects by type, name
    diff_pairs = sorted(diff_pairs, key=lambda x: x[0].key())

    for local_obj, remote_obj in diff_pairs:
        # Generate local YAML string
        local_dict = local_obj.to_dict(exclude_defaults=exclude_defaults)
        local_buf = StringIO()
        pretty_yaml(local_dict, out=local_buf, comments=False)
        local_lines = local_buf.getvalue().splitlines(keepends=True)

        # Generate remote YAML string (or empty for creates)
        if remote_obj is None:
            remote_lines = []
            local_label = f"local:{local_obj.key()[1]}"
            remote_label = "remote:<missing>"
        else:
            remote_dict = remote_obj.to_dict(exclude_defaults=exclude_defaults)
            remote_buf = StringIO()
            pretty_yaml(remote_dict, out=remote_buf, comments=False)
            remote_lines = remote_buf.getvalue().splitlines(keepends=True)
            local_label = f"local:{local_obj.key()[1]}"
            remote_label = f"remote:{remote_obj.key()[1]}"

        # Generate unified diff
        diff_lines = list(unified_diff(
            remote_lines, local_lines,
            fromfile=remote_label,
            tofile=local_label,
            lineterm='',
            n=context
        ))

        if diff_lines:
            secho("Differences:", tp='diff_label')
            for line in diff_lines:
                line = line.rstrip()
                if line.startswith('+'):
                    secho(line, tp='diff_added')
                elif line.startswith('-'):
                    secho(line, tp='diff_removed')
                elif line.startswith('?'):
                    secho(line, tp='diff_changed')
                else:
                    secho(line, tp='diff_unchanged')

    return len(diff_pairs)


# The end.

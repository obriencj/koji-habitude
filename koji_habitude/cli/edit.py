"""
koji_habitude.cli.edit

Edit remote koji objects interactively using an editor.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 4.5 Sonnet via Cursor
"""

from io import StringIO
from typing import List, Optional, Tuple

import click

from ..exceptions import ValidationError, YAMLError
from ..koji import session
from ..loader import load_all, pretty_yaml_all
from ..models import CORE_MODELS, BaseKey
from ..namespace import Namespace
from ..resolver import Resolver
from ..workflow import ApplyDictWorkflow, CompareDictWorkflow
from . import main
from .util import catchall, display_resolver_report, display_summary, sort_objects_for_output


def parse_names(args: List[str], default_type: str) -> List[BaseKey]:
    """
    Parse command line arguments into (type, name) tuples

    :param args: List of arguments like ['tag:foo', 'bar', 'user:bob']
    :param default_type: Type to use for untyped names
    :returns: List of (type, name) tuples
    """

    result = []
    for arg in args:
        if ':' in arg:
            type_part, name = arg.split(':', 1)
            result.append((type_part, name))
        else:
            result.append((default_type, arg))
    return result


def parse_yaml_from_string(yaml_content: str) -> List[dict]:
    """
    Parse YAML content from a string using the loader module

    :param yaml_content: The YAML content as a string
    :returns: List of parsed YAML documents
    :raises YAMLError: If YAML parsing fails
    """

    with StringIO(yaml_content) as fd:
        return list(load_all(fd))


def edit_and_validate(yaml_content: str) -> Optional[Tuple[str, List[dict]]]:
    """
    Edit YAML content and validate it. This is an interactive loop that allows
    the user to edit the YAML content, then we validate it, and repeat if
    there are problems

    :param yaml_content: The YAML content to edit
    :returns: Tuple of (edited_content, parsed_docs) if successful, (None,
        None) if cancelled
    """

    while True:
        # Invoke editor
        edited = click.edit(yaml_content, extension='.yaml', require_save=True)

        # If edit returns None, consider cancelled
        if edited is None:
            return None, None

        # Parse edited YAML using loader module
        try:
            yaml_docs = parse_yaml_from_string(edited)

            namespace = Namespace()
            namespace.feedall_raw(yaml_docs)
            namespace.expand()

        except YAMLError as e:
            click.echo(f"YAML parsing error: {e}", err=True)

        except (ValidationError, ValueError) as e:
            click.echo(f"Validation error: {e}", err=True)

        else:
            return (edited, yaml_docs)

        while True:
            choice = click.prompt("[E]dit / [Q]uit", default='E').upper()
            if "EDIT".startswith(choice):
                yaml_content = edited
                break
            elif "QUIT".startswith(choice):
                return None, None
            else:
                click.echo("Invalid choice. Please enter E or Q.", err=True)


@main.command()
@click.argument('names', nargs=-1, required=True)
@click.option(
    '--templates', "-t", metavar='PATH', multiple=True,
    help="Location to find templates that are not available in DATA")
@click.option(
    '--profile', "-p", default='koji',
    help="Koji profile to use for connection")
@click.option(
    "--include-defaults", "-d", default=False, is_flag=True,
    help="Whether to include default values (bool default: False)")
@click.option(
    '--type', 'default_type', default='tag',
    help="Default type for untyped names (default: tag)")
@click.option(
    '--show-unchanged', 'show_unchanged', is_flag=True, default=False,
    help="Show objects that don't need any changes")
@click.option(
    '--skip-phantoms', 'skip_phantoms', is_flag=True, default=False,
    help="Skip objects that have phantom dependencies")
@catchall
def edit(names, templates=None, profile='koji', include_defaults=False,
         default_type='tag', show_unchanged=False, skip_phantoms=False):
    """
    Edit remote koji objects interactively using an editor.

    Loads remote objects from koji, opens them in your editor for editing,
    validates the changes, shows a delta, and optionally applies them.

    \b
    NAMES can be:
      - TYPE:NAME (e.g., 'tag:foo', 'user:bob')
      - NAME (treated as default type, e.g., 'foo' -> 'tag:foo')

    \b
    Examples:
      - koji-habitude edit tag:foo
      - koji-habitude edit foo bar --type=target
      - koji-habitude edit tag:foo user:bob
    """

    # Parse names
    name_list = parse_names(names, default_type)
    for key in name_list:
        if key[0] not in CORE_MODELS:
            click.echo(f"Invalid type in key: {key}", err=True)
            return 1

    # Connect to koji (no auth, read-only)
    session_obj = session(profile, authenticate=False)

    # Use a Resolver to load remote objects
    resolver = Resolver(Namespace())

    # Resolve each (type, name) key
    for key in name_list:
        resolver.resolve(key)

    # Load remote references
    resolver.load_remote_references(session_obj, full=True)

    session_obj.logout()
    del session_obj

    # Get remote objects
    remotes = [ref.remote() for ref in resolver.report().discovered.values()]
    if not remotes:
        click.echo("No objects found to edit", err=True)
        return 1

    sorted_objects = sort_objects_for_output(remotes)

    # Output to StringIO buffer
    buffer = StringIO()
    exclude_defaults = not include_defaults
    series = (obj.to_dict(exclude_defaults=exclude_defaults) for obj in sorted_objects)
    pretty_yaml_all(series, out=buffer)
    yaml_content = buffer.getvalue()

    # Discard original loaded objects
    del remotes, sorted_objects, resolver

    # Main edit/compare/apply loop
    while True:
        # Edit and validate
        yaml_content, yaml_docs = edit_and_validate(yaml_content)
        if yaml_docs is None:
            click.echo("Edit cancelled", err=True)
            return 0

        # Perform compare run and output delta
        workflow = CompareDictWorkflow(
            objects=yaml_docs,
            template_paths=templates,
            profile=profile,
            skip_phantoms=skip_phantoms)
        workflow.run()

        display_summary(workflow.summary, show_unchanged=show_unchanged)
        display_resolver_report(workflow.resolver_report)

        del workflow

        # Prompt for action
        while True:
            choice = click.prompt("[A]pply / [E]dit / [Q]uit", default='Q').upper()
            if "APPLY".startswith(choice):
                # Apply changes
                apply_workflow = ApplyDictWorkflow(
                    objects=yaml_docs,
                    template_paths=templates,
                    profile=profile,
                    skip_phantoms=skip_phantoms)
                apply_workflow.run()

                display_summary(apply_workflow.summary, show_unchanged=False)
                display_resolver_report(apply_workflow.resolver_report)

                return 0

            elif "EDIT".startswith(choice):
                # Back into the edit loop
                break

            elif "QUIT".startswith(choice):
                return 0

            else:
                click.echo("Invalid choice. Please enter A, E, or Q.", err=True)


# The end.

"""
koji_habitude.cli

Main CLI interface using clique with orchestration of the
synchronization process.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated with Human Rework


import sys
from pathlib import Path
from typing import Optional, List, Tuple

import click

from .loader import MultiLoader, YAMLLoader, pretty_yaml_all
from .namespace import Namespace, TemplateNamespace, ExpanderNamespace


def resplit(strs: List[str], sep=',') -> List[str]:
    return list(filter(None, map(str.strip, sep.join(strs).split(sep))))


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
    '--dry-run', 'dry_run', is_flag=True,
    help="Show what would be done without making changes")
@click.argument('data', nargs=-1, required=True)
def sync(templates, profile, offline, dry_run, data):

    # TODO
    pass


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
@click.argument('data', nargs=-1, required=True)
def diff(templates, profile, offline, data):

    """
    Show what changes would be made without applying them.

    This is a convenience alias for 'sync --dry-run'.

    DATA can be directories or files containing YAML object definitions.
    """

    # Call sync with dry_run=True
    return sync(templates, profile, offline, True, data)


@click.command()
@click.option(
    '--templates', "-T", 'template_dirs', metavar='PATH', multiple=True,
    help="Load only templates from the given paths")
@click.option(
    '--yaml', 'yaml', is_flag=True, default=False,
    help="Show expanded templates as yaml")
@click.option(
    '--full', 'full', is_flag=True, default=False,
    help="Show full template details")
@click.option(
    '--select', "-S", 'select', metavar='NAME', multiple=True,
    help="Select templates by name")
@click.argument('dirs', metavar='PATH', nargs=-1, required=False)
def list_templates(dirs=[], template_dirs=[], yaml=False, full=False, select=[]):
    """
    List available templates.

    Shows all templates found in the given locations with their
    configuration details.

    Accepts --templates to load only templates from the given paths. Positional
    path arguments are treated the same way, but we support both styles to mimic
    the invocation pattern of other commands in this tool.

    PATH can be directories containing template files.
    """

    ns = TemplateNamespace()
    ml = MultiLoader([YAMLLoader])
    if template_dirs:
        ns.feedall_raw(ml.load(template_dirs))
    if dirs:
        ns.feedall_raw(ml.load(dirs))
    ns.expand()

    if select:
        expanded = (tmpl for tmpl in ns._templates.values() if tmpl.name in select)
    else:
        expanded = ns._templates.values()

    if yaml:
        pretty_yaml_all((obj.to_dict() for obj in expanded))
        return

    for tmpl in expanded:
        print(f"{tmpl.name}")
        if full:
            print(f"  declared at: {tmpl.filename}:{tmpl.lineno}")
            if tmpl.trace:
                print("  expanded from:")
                for step in tmpl.trace:
                    print(f"    {step['name']} at {step['file']}:{step['line']}")
            print(f"  schema: {tmpl.schema}")
            if tmpl.defaults:
                print("  defaults:")
                for var, value in tmpl.defaults.items():
                    print(f"    {var}: {value!r}")
            missing = tmpl.get_missing()
            if missing:
                print(f"  required:")
                for var in missing:
                    print(f"    {var}")
            if tmpl.template_file:
                print(f"  content: <file: {tmpl.template_file}>")
            else:
                print(f"  content: '''\n{tmpl.template_content}\n''' # end content for {tmpl.name}")
        else:
            if tmpl.defaults:
                print("  defaults:")
                for var, value in tmpl.defaults.items():
                    print(f"    {var}: {value!r}")
            missing = tmpl.get_missing()
            if missing:
                print(f"  required:")
                for var in missing:
                    print(f"    {var}")
        print()


@click.command()
@click.option(
    '--templates', 'templates', metavar='PATH', multiple=True,
    help="Location to find templates that are not available in DATA")
@click.argument('data', nargs=-1, required=True)
def validate(templates, data):
    """
    Validate data files and templates.

    Loads and validates all templates and data files without connecting to koji.

    DATA can be directories or files containing YAML object definitions.
    """

    pass


@click.command()
@click.option(
    '--templates', 'templates', metavar='PATH', multiple=True,
    help="Location to find templates that are not available in DATA")
@click.argument('data', metavar='DATA', nargs=-1, required=True)
def expand(templates, profile, offline, data):
    """
    Expand templates and data files into YAML output.

    Loads templates from --templates locations, then processes DATA files
    through template expansion and outputs the final YAML content.

    DATA can be directories or files containing YAML object definitions.
    """

    import yaml

    # Load templates into TemplateNamespace
    template_ns = TemplateNamespace()
    if templates:
        ml = MultiLoader([YAMLLoader])
        template_ns.feedall_raw(ml.load(templates))
        template_ns.expand()

    # Create ExpanderNamespace with the loaded templates
    expander_ns = ExpanderNamespace()
    expander_ns._templates.update(template_ns._templates)

    # Load and process data files
    ml = MultiLoader([YAMLLoader])
    expander_ns.feedall_raw(ml.load(data))
    expander_ns.expand()

    # Output all objects as YAML
    expanded = expander_ns._ns.values()
    pretty_yaml_all(obj.data for obj in expanded)


@click.group()
def main():
    """
    koji-habitude - Synchronize local koji data expectations with hub instance.

    This tool loads YAML templates and data files, resolves dependencies,
    and applies changes to a koji hub in the correct order.
    """

    pass


# Register subcommands
main.add_command(sync)
main.add_command(diff)
main.add_command(list_templates)
main.add_command(validate)
main.add_command(expand)



if __name__ == '__main__':
    sys.exit(main())


# The end.

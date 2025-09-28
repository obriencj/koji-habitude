"""
koji_habitude.cli.templates

List templates.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""


import click

from ..loader import MultiLoader, YAMLLoader, pretty_yaml_all
from ..namespace import TemplateNamespace
from ..templates import Template

from . import main


def print_template(tmpl: Template, full: bool = False):
    print(f"{tmpl.name}")
    if full:
        print(f"  declared at: {tmpl.filename}:{tmpl.lineno}")
        if tmpl.trace:
            print("  expanded from:")
            for step in tmpl.trace:
                print(f"    {step['name']} at {step['file']}:{step['line']}")
        if tmpl.template_schema:
            print(f"  schema: {tmpl.template_schema}")
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


@main.command()
@click.argument('dirs', metavar='PATH', nargs=-1, required=False)
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
        expanded = (tmpl for tmpl in ns.templates() if tmpl.name in select)
    else:
        expanded = ns.templates()

    if yaml:
        pretty_yaml_all((obj.to_dict() for obj in expanded))
        return

    for tmpl in expanded:
        print_template(tmpl, full)
        print()


# The end.

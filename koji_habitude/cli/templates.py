"""
koji_habitude.cli.templates

List templates.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""


from pathlib import Path
from typing import Any, Dict, List

import click

from . import main
from ..loader import load_yaml_files, pretty_yaml, pretty_yaml_all
from ..namespace import ExpanderNamespace, Namespace, TemplateNamespace
from ..templates import Template
from ..workflow import ApplyDictWorkflow, CompareDictWorkflow
from .util import catchall, display_resolver_report, display_summary


def call_from_args(
    template_name: str,
    variables: List[str]) -> Dict[str, Any]:

    data = {
        '__file__': "<user-input>",
        'type': template_name,
    }

    for var in variables:
        if '=' not in var:
            key, value = var, ''
        else:
            key, value = var.split('=', 1)
        data[key] = value

    return data


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
            print(f"  content: '''\n{tmpl.template_content}\n"
                  f"''' # end content for {tmpl.name}")
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
@catchall
def list_templates(
        dirs=[],
        template_dirs=[],
        yaml=False,
        full=False,
        select=[]):
    """
    List available templates.

    Shows all templates found in the given locations with their
    configuration details.

    Accepts `--templates` to load only templates from the given
    paths. Positional path arguments are treated the same way, but we
    support both styles to mimic the invocation pattern of other
    commands in this tool.

    PATH can be directories containing template files.
    """

    ns = TemplateNamespace()
    if template_dirs:
        ns.feedall_raw(load_yaml_files(template_dirs))
    if dirs:
        ns.feedall_raw(load_yaml_files(dirs))
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


@main.group('template')
def template():
    """
    Manage and work with individual templates.

    This command group provides operations for listing, expanding,
    comparing, and applying individual templates.
    """

    pass


@template.command('show')
@click.argument('template_name', metavar='NAME')
@click.option(
    '--templates', '-T', 'template_dirs', metavar='PATH', multiple=True,
    help="Load only templates from the given paths")
@click.option(
    '--yaml', 'yaml', is_flag=True, default=False,
    help="Template definition as yaml")
@catchall
def template_show(
        template_name,
        template_dirs=[],
        yaml=False):
    """
    Show the definition of a single template.

    NAME is the name of the template to show the definition of.
    """

    tns = TemplateNamespace()
    if not template_dirs:
        template_dirs = list(Path.cwd().glob('*.yml'))
        template_dirs.extend(Path.cwd().glob('*.yaml'))

    tns.feedall_raw(load_yaml_files(template_dirs))
    tns.expand()

    tmpl = tns.get_template(template_name)
    if not tmpl:
        click.echo(f"Template {template_name} not found", err=True)
        return 1

    if yaml:
        pretty_yaml(tmpl.to_dict())
        return

    print_template(tmpl, full)
    click.echo()


@template.command('expand')
@click.argument('template_name', metavar='NAME')
@click.argument('variables', metavar='KEY=VALUE', nargs=-1)
@click.option(
    '--templates', '-T', 'template_dirs', metavar='PATH', multiple=True,
    help="Load templates from the given paths")
@click.option(
    '--validate', 'validate', is_flag=True, default=False,
    help="Validate the expanded template")
@catchall
def template_expand(
        template_name,
        variables=[],
        template_dirs=[],
        validate=False):
    """
    Expand a single template and show the result.

    NAME is the name of the template to expand with the given KEY=VALUE variables
    """

    tns = TemplateNamespace()
    if not template_dirs:
        template_dirs = list(Path.cwd().glob('*.yml'))
        template_dirs.extend(Path.cwd().glob('*.yaml'))

    tns.feedall_raw(load_yaml_files(template_dirs))
    tns.expand()

    ns = Namespace() if validate else ExpanderNamespace()
    ns.merge_templates(tns)

    ns.feed_raw(call_from_args(template_name, variables))
    ns.expand()

    if validate:
        results = (obj.to_dict() for obj in ns.values())
    else:
        results = (obj.data for obj in ns.values())

    pretty_yaml_all(results)


@template.command('compare')
@click.argument('template_name', metavar='NAME')
@click.argument('variables', metavar='KEY=VALUE', nargs=-1)
@click.option(
    '--templates', '-T', 'template_dirs', metavar='PATH', multiple=True,
    help="Load templates from the given paths")
@click.option(
    '--profile', default='koji',
    help="Koji profile to use for connection")
@click.option(
    '--show-unchanged', 'show_unchanged', is_flag=True, default=False,
    help="Show objects that don't need any changes")
@catchall
def template_compare(
        template_name,
        variables=[],
        template_dirs=[],
        profile='koji',
        show_unchanged=False):
    """
    Compare a single template expansion with koji.

    NAME is the name of the template to expand with the given KEY=VALUE variables

    The expanded objects will then be compared with the objects on the koji instance.
    """

    data = call_from_args(template_name, variables)

    if not template_dirs:
        template_dirs = list(Path.cwd().glob('*.yml'))
        template_dirs.extend(Path.cwd().glob('*.yaml'))

    workflow = CompareDictWorkflow(
        objects=[data],
        template_paths=template_dirs,
        profile=profile,
    )
    workflow.run()

    display_summary(workflow.summary, show_unchanged)
    display_resolver_report(workflow.resolver_report)

    return 1 if workflow.resolver_report.phantoms else 0


@template.command('apply')
@click.argument('template_name', metavar='NAME')
@click.argument('variables', metavar='KEY=VALUE', nargs=-1)
@click.option(
    '--templates', '-T', 'template_dirs', metavar='PATH', multiple=True,
    help="Load templates from the given paths")
@click.option(
    '--profile', default='koji',
    help="Koji profile to use for connection")
@click.option(
    '--show-unchanged', 'show_unchanged', is_flag=True, default=False,
    help="Show objects that don't need any changes")
@catchall
def template_apply(
        template_name,
        variables=[],
        template_dirs=[],
        profile='koji',
        show_unchanged=False):
    """
    Apply a single template expansion with koji.

    NAME is the name of the template to expand with the given KEY=VALUE variables

    The expanded objects will then be compared against and applied to the koji instance.
    """

    data = call_from_args(template_name, variables)

    if not template_dirs:
        template_dirs = list(Path.cwd().glob('*.yml'))
        template_dirs.extend(Path.cwd().glob('*.yaml'))

    workflow = ApplyDictWorkflow(
        objects=[data],
        template_paths=template_dirs,
        profile=profile,
    )
    workflow.run()

    display_summary(workflow.summary, show_unchanged)
    display_resolver_report(workflow.resolver_report)

    return 1 if workflow.resolver_report.phantoms else 0


# The end.

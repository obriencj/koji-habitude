"""
koji_habitude.cli.templates

List templates.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 4.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Assisted, Mostly Human


from pathlib import Path
from typing import Any, Dict, List

import click
from click import echo
from yaml import safe_load

from ..loader import load_yaml_files, pretty_yaml, pretty_yaml_all
from ..namespace import ExpanderNamespace, Namespace, TemplateNamespace
from ..templates import Template
from ..workflow import ApplyDictWorkflow, CompareDictWorkflow
from . import main
from .theme import select_theme
from .util import (catchall, display_resolver_report, display_summary,
                   display_summary_as_diff)


def call_from_args(
        template_name: str,
        variables: List[str]) -> Dict[str, Any]:
    """
    Construct a TemplateCall yaml document from the given template
    name and variables.

    :param template_name: The name of the template to call
    :param variables: The variables to pass to the template
    :returns: A dictionary representing the TemplateCall yaml document
    """

    data = {
        '__file__': "<user-input>",
        'type': template_name,
    }

    for var in variables:
        if '=' not in var:
            key, value = var, ''
        else:
            key, value = var.split('=', 1)
        data[key] = safe_load(value)

    return data


def print_template(tmpl: Template, full: bool = False, theme=None):
    """
    Print template information with themed styling.
    """

    if theme is None:
        theme = select_theme()

    style = theme.style

    echo(style("Template: ", tp='template_label') + style(tmpl.name, tp='template_name'))
    if tmpl.description:
        echo(style(tmpl.description, tp='template_description'))

    if tmpl.template_model:
        # Display model information instead of missing/defaults
        model = tmpl.template_model
        if model.name and model.name != 'model':
            echo(style("Model: ", tp='template_label') + style(model.name, tp='template_value'))
        if model.description:
            echo(style(model.description, tp='template_description'))

        # Separate fields into required and optional
        required_fields = []
        optional_fields = []

        for field_name, field_def in model.fields.items():
            display_name = field_def.alias if field_def.alias else field_name
            field_info = display_name

            # Add type information
            field_info += f" ({field_def.type})"

            # Add description if present
            if field_def.description:
                field_info += f": {field_def.description}"

            # Add default value if present
            if field_def.default is not None:
                field_info += f" = {field_def.default!r}"

            if field_def.required:
                required_fields.append(field_info)
            else:
                optional_fields.append(field_info)

        if required_fields:
            echo(style("Required: ", tp='template_label'))
            for field_info in required_fields:
                echo(f"  {style(field_info, tp='template_value')}")

        if optional_fields:
            echo(style("Optional: ", tp='template_label'))
            for field_info in optional_fields:
                echo(f"  {style(field_info, tp='template_value')}")

    else:
        # Original behavior: display missing/defaults
        missing = tmpl.get_missing()
        if missing:
            echo(style("Required: ", tp='template_label'))
            for var in missing:
                echo(f"  {style(var, tp='template_value')}")
        if tmpl.defaults:
            echo(style("Optional: ", tp='template_label'))
            for var, value in tmpl.defaults.items():
                echo(f"  {style(var, tp='template_value')}: {value!r}")

    if full:
        echo(style("Declared at: ", tp='template_label') + f"{tmpl.filename}:{tmpl.lineno}")
        if tmpl.trace:
            echo(style("Expanded from: ", tp='template_label'))
            for step in tmpl.trace:
                echo(f"  {step['name']} at {step['file']}:{step['line']}")
        # if tmpl.template_schema:
        #     echo(style("Schema:", tp='template_label') + f"{tmpl.template_schema}")
        if tmpl.template_file:
            echo(style("Content:", tp='template_label') + f"<file: {tmpl.template_file}>")
        else:
            echo(style("Content:", tp='template_label') + " '''\n" +
                 style(f"{tmpl.template_content}\n", tp='template_content') +
                 "''' " + style(f"# end content for {tmpl.name}", tp='template_comment'))


def opt_template_path(fn):
    fn = click.option(
        '--templates', "-t", 'template_dirs', metavar='PATH', multiple=True,
        help="Load only templates from the given paths")(fn)
    fn = click.option(
        '--recursive', '-r', is_flag=True, default=False,
        help="Search template and data directories recursively")(fn)
    return fn


def opt_profile(fn):
    fn = click.option(
        '--profile', "-p", default='koji',
        help="Koji profile to use for connection")(fn)
    return fn


@main.command()
@click.argument('dirs', metavar='PATH', nargs=-1, required=False)
@opt_template_path
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
        recursive=False,
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
        ns.feedall_raw(load_yaml_files(template_dirs, recursive=recursive))
    if dirs:
        ns.feedall_raw(load_yaml_files(dirs, recursive=recursive))
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
@opt_template_path
@click.option(
    '--yaml', 'yaml', is_flag=True, default=False,
    help="Template definition as yaml")
@click.option(
    '--full', 'full', is_flag=True, default=False,
    help="Show full template details")
@catchall
def template_show(
        template_name,
        template_dirs=[],
        recursive=False,
        yaml=False,
        full=False):
    """
    Show the definition of a single template.

    NAME is the name of the template to show the definition of.
    """

    tns = TemplateNamespace()
    if not template_dirs:
        template_dirs = list(Path.cwd().glob('*.yml'))
        template_dirs.extend(Path.cwd().glob('*.yaml'))

    tns.feedall_raw(load_yaml_files(template_dirs, recursive=recursive))
    tns.expand()

    tmpl = tns.get_template(template_name)
    if not tmpl:
        click.echo(f"Template {template_name} not found", err=True)
        return 1

    if yaml:
        pretty_yaml(tmpl.to_dict(exclude_defaults=True))
        return

    print_template(tmpl, full)
    click.echo()


@template.command('expand')
@click.argument('template_name', metavar='NAME')
@click.argument('variables', metavar='KEY=VALUE', nargs=-1)
@opt_template_path
@click.option(
    '--validate', 'validate', is_flag=True, default=False,
    help="Validate the expanded template")
@catchall
def template_expand(
        template_name,
        recursive=False,
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

    tns.feedall_raw(load_yaml_files(template_dirs, recursive=recursive))
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
@opt_template_path
@opt_profile
@click.option(
    '--show-unchanged', 'show_unchanged', is_flag=True, default=False,
    help="Show objects that don't need any changes")
@catchall
def template_compare(
        template_name,
        variables=[],
        template_dirs=[],
        recursive=False,
        profile='koji',
        show_unchanged=False):
    """
    Expand a single template and compare the result with koji.

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
        recursive=recursive,
        profile=profile,
    )
    workflow.run()

    display_summary(workflow.summary, show_unchanged)
    display_resolver_report(workflow.resolver_report)

    return 1 if workflow.resolver_report.phantoms else 0


@template.command('diff')
@click.argument('template_name', metavar='NAME')
@click.argument('variables', metavar='KEY=VALUE', nargs=-1)
@opt_template_path
@opt_profile
@click.option(
    '--include-defaults', '-d', default=False, is_flag=True,
    help="Whether to include default values (bool default: False)")
@click.option(
    '--context', '-c', default=3, type=int, metavar='N',
    help="Number of context lines around each change (default: 3)")
@catchall
def template_diff(
        template_name,
        variables=[],
        template_dirs=[],
        recursive=False,
        profile='koji',
        include_defaults=False,
        context=3):
    """
    Expand a single template and compare the result with koji.

    NAME is the name of the template to expand with the given KEY=VALUE variables

    Results will be displayed as a unified diff between the expanded and
    validated template and the koji state of the expanded objects.
    """

    data = call_from_args(template_name, variables)

    if not template_dirs:
        template_dirs = list(Path.cwd().glob('*.yml'))
        template_dirs.extend(Path.cwd().glob('*.yaml'))

    workflow = CompareDictWorkflow(
        objects=[data],
        template_paths=template_dirs,
        recursive=recursive,
        profile=profile,
    )
    workflow.run()

    exclude_defaults = not include_defaults
    diffcount = display_summary_as_diff(
        workflow.summary,
        context=context,
        exclude_defaults=exclude_defaults)

    return 0 if not diffcount else 1


@template.command('apply')
@click.argument('template_name', metavar='NAME')
@click.argument('variables', metavar='KEY=VALUE', nargs=-1)
@opt_template_path
@opt_profile
@click.option(
    '--show-unchanged', 'show_unchanged', is_flag=True, default=False,
    help="Show objects that don't need any changes")
@catchall
def template_apply(
        template_name,
        variables=[],
        template_dirs=[],
        recursive=False,
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
        recursive=recursive,
        profile=profile,
    )
    workflow.run()

    display_summary(workflow.summary, show_unchanged)
    display_resolver_report(workflow.resolver_report)

    return 1 if workflow.resolver_report.phantoms else 0


# The end.

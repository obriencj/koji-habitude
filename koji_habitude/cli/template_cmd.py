"""
koji_habitude.cli.template_cmd

Template command group for working with individual templates.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""


import click
from pathlib import Path

from . import main
from ..loader import load_yaml_files, pretty_yaml_all
from ..namespace import TemplateNamespace, ExpanderNamespace, Namespace
from ..templates import Template
from .util import catchall, resplit, display_summary, display_resolver_report
from ..workflow import CompareDictWorkflow


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
            print(f"  content: '''\n{tmpl.template_content}\n'''"
                  " # end content for {tmpl.name}")
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


@main.group('template')
def template():
    """
    Manage and work with individual templates.

    This command group provides operations for listing, expanding,
    comparing, and applying individual templates.
    """

    pass


@template.command('list')
@click.option(
    '--templates', '-T', 'template_dirs', metavar='PATH', multiple=True,
    help="Load only templates from the given paths")
@click.option(
    '--yaml', 'yaml', is_flag=True, default=False,
    help="Show expanded templates as yaml")
@click.option(
    '--full', 'full', is_flag=True, default=False,
    help="Show full template details")
@click.option(
    '--select', '-S', 'select', metavar='NAME', multiple=True,
    help="Select templates by name")
@catchall
def template_list(
        dirs=[],
        template_dirs=[],
        yaml=False,
        full=False,
        select=[]):
    """
    List available templates from the paths specified with --templates. If no
    paths are specified, then the YAML files in the current working directory is
    used.
    """

    ns = TemplateNamespace()
    if template_dirs:
        ns.feedall_raw(load_yaml_files(template_dirs))
    else:
        ns.feedall_raw(load_yaml_files([Path.cwd()]))
    ns.expand()

    if select:
        select = resplit(select)
        expanded = (tmpl for tmpl in ns.templates() if tmpl.name in select)
    else:
        expanded = ns.templates()

    if yaml:
        pretty_yaml_all((obj.to_dict() for obj in expanded))
        return

    for tmpl in expanded:
        print_template(tmpl, full)
        print()


@template.command('expand')
@click.argument('template_name', metavar='NAME')
@click.option(
    '--templates', '-T', 'template_dirs', metavar='PATH', multiple=True,
    help="Load templates from the given paths")
@click.option(
    '--var', '-V', 'variables', metavar='KEY=VALUE', multiple=True,
    help="Set template variable (can be specified multiple times)")
@click.option(
    '--validate', 'validate', is_flag=True, default=False,
    help="Validate the expanded template")
@catchall
def template_expand(
        template_name,
        template_dirs=[],
        variables=[],
        validate=False):
    """
    Expand a single template and show the result.

    NAME is the name of the template to expand.

    PATH can be directories containing template files.

    Use --var to provide template variables, e.g.:
      --var name=mytag --var arches=x86_64
    """

    tns = TemplateNamespace()
    if template_dirs:
        tns.feedall_raw(load_yaml_files(template_dirs))
    else:
        tns.feedall_raw(load_yaml_files([Path.cwd()]))
    tns.expand()

    ns = Namespace() if validate else ExpanderNamespace()
    ns.merge_templates(tns)

    tc = {
        '__file__': "<user-input>",
        'type': template_name,
    }
    for var in variables:
        if '=' not in var:
            key, value = var, ''
        else:
            key, value = var.split('=', 1)
        tc[key] = value
    ns.feed_raw(tc)
    ns.expand()

    if validate:
        results = (obj.to_dict() for obj in ns.values())
    else:
        results = (obj.data for obj in ns.values())

    pretty_yaml_all(results)


@template.command('compare')
@click.argument('template_name', metavar='NAME')
@click.option(
    '--templates', '-T', 'template_dirs', metavar='PATH', multiple=True,
    help="Load templates from the given paths")
@click.option(
    '--var', '-V', 'variables', metavar='KEY=VALUE', multiple=True,
    help="Set template variable (can be specified multiple times)")
@click.option(
    '--profile', default='koji',
    help="Koji profile to use for connection")
@click.option(
    '--show-unchanged', 'show_unchanged', is_flag=True, default=False,
    help="Show objects that don't need any changes")
@catchall
def template_compare(
        template_name,
        template_dirs=[],
        variables=[],
        profile='koji',
        show_unchanged=False):
    """
    Compare a single template expansion with koji.

    NAME is the name of the template to expand and compare.

    PATH can be directories containing template files.

    Use --var to provide template variables.
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
        data[key] = value


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
@click.option(
    '--templates', '-T', 'template_dirs', metavar='PATH', multiple=True,
    help="Load templates from the given paths")
@click.option(
    '--var', '-V', 'variables', metavar='KEY=VALUE', multiple=True,
    help="Set template variable (can be specified multiple times)")
@click.option(
    '--profile', default='koji',
    help="Koji profile to use for connection")
@click.option(
    '--show-unchanged', 'show_unchanged', is_flag=True, default=False,
    help="Show objects that don't need any changes")
@catchall
def template_apply(
        template_name,
        dirs=[],
        template_dirs=[],
        variables=[],
        profile='koji',
        show_unchanged=False):
    """
    Apply a single template expansion to koji.

    NAME is the name of the template to expand and apply.

    PATH can be directories containing template files.

    Use --var to provide template variables.
    """

    # TODO: Implementation - expand template and apply to koji
    print(f"template apply {template_name} - not yet implemented")


# The end.

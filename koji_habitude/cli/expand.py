"""
koji_habitude.cli.expand

Expand templates and data files into YAML output.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 3.5 Sonnet via Cursor
"""


import click

from . import main
from ..loader import load_yaml_files, pretty_yaml_all
from ..namespace import (
    ExpanderNamespace, Namespace, Redefine, TemplateNamespace,
)
from .util import catchall, resplit, sort_objects_for_output


@main.command()
@click.argument('data', metavar='DATA', nargs=-1, required=True)
@click.option(
    '--templates', "-t", metavar='PATH', multiple=True,
    help="Location to find templates that are not available in DATA")
@click.option(
    '--recursive', '-r', is_flag=True, default=False,
    help="Search template and data directories recursively")
@click.option(
    '--validate', 'validate', is_flag=True, default=False,
    help="Validate the expanded templates and data files")
@click.option(
    "--include-defaults", "-d", default=False, is_flag=True,
    help="Whether to include default values (bool default: False)")
@click.option(
    "--no-comments", is_flag=True, default=False,
    help="Do not include comments in the output")
@click.option(
    "--select", "-S", "select", metavar="NAME", multiple=True,
    help="Filter results to only include types")
@catchall
def expand(data, templates=None, recursive=False,
           validate=False, include_defaults=False, no_comments=False,
           select=[]):
    """
    Expand templates and data files into YAML output.

    Loads templates from --templates locations, then processes DATA
    files through template expansion and outputs the final YAML
    content.

    DATA can be directories or files containing YAML object
    definitions.
    """

    namespace = Namespace() if validate else ExpanderNamespace()
    for typename in select:
        if typename not in namespace.typemap:
            raise ValueError(f"Type {typename} not present in namespace")

    # Load templates into TemplateNamespace
    template_ns = TemplateNamespace()
    if templates:
        template_ns.feedall_raw(load_yaml_files(templates, recursive=recursive))
        template_ns.expand()

    namespace.merge_templates(template_ns, redefine=Redefine.ALLOW)

    # Load and process data files
    namespace.feedall_raw(load_yaml_files(data, recursive=recursive))
    namespace.expand()

    select = resplit(select)
    if select:
        results = (obj for obj in namespace.values()
                   if obj.typename in select)
    else:
        results = namespace.values()

    results = sort_objects_for_output(results)

    # Output all objects as YAML
    if validate:
        exclude_defaults = not include_defaults
        # if we're validating, let pydantic provide the fully
        # validated objects
        results = (obj.to_dict(exclude_defaults=exclude_defaults) for obj in results)
    else:
        # if we're not validating, use the raw data
        results = (obj.data for obj in results)

    pretty_yaml_all(results, comments=not no_comments)


# The end.

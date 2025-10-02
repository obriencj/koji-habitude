"""
koji_habitude.cli.expand

Expand templates and data files into YAML output.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""


import click

from . import main
from ..loader import load_yaml_files, pretty_yaml_all
from ..namespace import ExpanderNamespace, Namespace, TemplateNamespace
from .util import catchall, resplit


@main.command()
@click.argument('data', metavar='DATA', nargs=-1, required=True)
@click.option(
    '--templates', 'templates', metavar='PATH', multiple=True,
    help="Location to find templates that are not available in DATA")
@click.option(
    '--validate', 'validate', is_flag=True, default=False,
    help="Validate the expanded templates and data files")
@click.option(
    "--select", "-S", "select", metavar="NAME", multiple=True,
    help="Filter results to only include types")
@catchall
def expand(data, templates=None, validate=False, select=[]):
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
        template_ns.feedall_raw(load_yaml_files(templates))
        template_ns.expand()

    namespace._templates.update(template_ns._templates)

    # Load and process data files
    namespace.feedall_raw(load_yaml_files(data))
    namespace.expand()

    select = resplit(select)
    if select:
        results = (obj for obj in namespace.values()
                   if obj.typename in select)
    else:
        results = namespace.values()

    # Output all objects as YAML
    if validate:
        # if we're validating, let pydantic provide the fully
        # validated objects
        results = (obj.to_dict() for obj in results)
    else:
        # if we're not validating, use the raw data
        results = (obj.data for obj in results)

    pretty_yaml_all(results)


# The end.

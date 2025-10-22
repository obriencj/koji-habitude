"""
koji_habitude.cli.fetch

Fetch remote data from Koji instance and output as YAML.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 4.5 Sonnet via Cursor
"""


import click
import sys

from . import main
from ..loader import pretty_yaml_all
from ..resolver import Reference
from ..workflow import CompareWorkflow
from .util import catchall


@main.command()
@click.argument('data', nargs=-1, required=True)
@click.option(
    '--templates', 'templates', metavar='PATH', multiple=True,
    help="Location to find templates that are not available in DATA")
@click.option(
    '--profile', "-p", default='koji',
    help="Koji profile to use for connection")
@click.option(
    "--output", "-o", default=sys.stdout, type=click.File('w'), metavar='PATH',
    help="Path to output YAML file (default: stdout)")
@catchall
def fetch(data, templates=None, profile='koji', output=sys.stdout):
    """
    Fetch remote data from Koji instance and output as YAML.

    Loads templates and data files, resolves dependencies, connects to
    Koji, and outputs YAML documents representing the remote state of
    all objects that exist on the Koji instance.

    DATA can be directories or files containing YAML object definitions.
    """

    workflow = CompareWorkflow(
        paths=data,
        template_paths=templates,
        profile=profile)
    workflow.run()

    # Filter to only CoreObjects with remote data (skip References and phantoms)
    remote_objects = []
    for obj in workflow.dataseries:
        if isinstance(obj, Reference):
            continue  # Skip all References
        remote = obj.remote()
        if remote is not None:
            remote_objects.append(remote.to_dict())

    # Output all remote objects as YAML
    pretty_yaml_all(remote_objects, out=output)

    return 0


# The end.

"""
koji_habitude.cli

Main CLI interface using clique with orchestration of the
synchronization process.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated with Human Rework


from typing import List

import click


from .sync import sync
from .diff import diff
from .templates import list_templates
from .expand import expand

import os
import logging


# Get the log level from the environment variable, defaulting to 'INFO' if not set
log_level = os.environ.get('LOGLEVEL', 'INFO').upper()

# Configure basic logging with the determined level
logging.basicConfig(level=log_level)


def resplit(strs: List[str], sep=',') -> List[str]:
    return list(filter(None, map(str.strip, sep.join(strs).split(sep))))


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
main.add_command(expand)



# The end.

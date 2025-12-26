"""
koji_habitude.cli

Main CLI interface using clique with orchestration of the
synchronization process.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated with Human Rework


import logging
import os

import click


class MagicGroup(click.Group):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context_settings = {
            "help_option_names": ["-h", "--help"],
        }

    def _load_commands(self):
        # delaying to avoid circular imports
        from . import apply
        from . import compare
        from . import templates
        from . import expand
        from . import fetch
        from . import dump
        from . import diff
        from . import edit

    def get_command(self, ctx, cmd_name):
        self._load_commands()
        return super().get_command(ctx, cmd_name)

    def list_commands(self, ctx):
        self._load_commands()
        return super().list_commands(ctx)


@click.group(cls=MagicGroup)
def main():
    """
    koji-habitude - Synchronize local koji data expectations with
    hub instance.

    This tool loads YAML templates and data files, resolves
    dependencies, and applies changes to a koji hub in the correct
    order.
    """

    log_level = os.environ.get('LOGLEVEL', '').strip().upper()
    if log_level:
        logging.basicConfig(level=log_level)


# The end.

"""
koji_habitude.cli

Main CLI interface using clique with orchestration of the
synchronization process.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 3.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated with Human Rework


import logging
import os
from typing import List

import click
from pydantic import ValidationError

from koji import GSSAPIError, GenericError


def resplit(strs: List[str], sep=',') -> List[str]:
    """
    Takes a list of strings which may be comma-separated to indicate multiple
    values. Returns a list of strings with the commas removed and those values
    expanded, whitespace stripped, and any empty strings omitted.

    Example:
        >>> resplit(['foo', ' ', 'bar,baz', 'qux,,quux'])
        ['foo', 'bar', 'baz', 'qux', 'quux']
    """

    # joins 'em, splits 'em, strips 'em, and filters 'em
    return list(filter(None, map(str.strip, sep.join(strs).split(sep))))


class MagicGroup(click.Group):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # delaying to avoid circular imports
        from .sync import sync
        from .diff import diff
        from .templates import list_templates
        from .expand import expand

        self.add_command(sync)
        self.add_command(diff)
        self.add_command(list_templates)
        self.add_command(expand)


    def __call__(self, *args, **kwargs):
        try:
            return super().__call__(*args, **kwargs)

        except ValidationError as e:
            click.echo(f"[ValidationError] {e}", err=True)
            return 1

        except GSSAPIError as e:
            click.echo(f"[GSSAPIError] {e}", err=True)
            return 1

        except GenericError as e:
            click.echo(f"[GenericError] {e}", err=True)
            return 1

        except KeyboardInterrupt:
            click.echo("[Keyboard interrupt]", err=True)
            return 130

        except Exception as e:
            logger.error(f"Error: {e}")
            raise


@click.group(cls=MagicGroup)
def main():
    """
    koji-habitude - Synchronize local koji data expectations with hub instance.

    This tool loads YAML templates and data files, resolves dependencies,
    and applies changes to a koji hub in the correct order.
    """

    log_level = os.environ.get('LOGLEVEL', 'WARNING').upper()
    logging.basicConfig(level=log_level)


# The end.

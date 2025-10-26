"""
koji_habitude.cli.theme

Color theme system for CLI output.

:author: Christopher O'Brien <obriencj@gmail.com>
:license: GNU General Public License v3
:ai-assistant: Claude 4.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated, Human Rework


from dataclasses import dataclass, field
import os
from typing import Any, Dict

from click import echo, style


__all__ = (
    'ColorTheme',
    'NoColorTheme',

    'DEFAULT_THEME',
    'NOCOLOR_THEME',

    'select_theme',
)


@dataclass
class ColorTheme:

    type_heading: Dict[str, Any] = field(default_factory=lambda: {'fg': 'yellow'})
    object_name: Dict[str, Any] = field(default_factory=lambda: {'fg': 'white'})
    create: Dict[str, Any] = field(default_factory=lambda: {'fg': 'green'})
    update: Dict[str, Any] = field(default_factory=lambda: {'fg': 'cyan'})
    add: Dict[str, Any] = field(default_factory=lambda: {'fg': 'blue'})
    remove: Dict[str, Any] = field(default_factory=lambda: {'fg': 'red'})
    modify: Dict[str, Any] = field(default_factory=lambda: {'fg': 'magenta'})
    summary_text: Dict[str, Any] = field(default_factory=lambda: {'fg': 'bright_white'})
    unchanged_text: Dict[str, Any] = field(default_factory=lambda: {'fg': 'bright_black'})

    # used in template show
    template_label: Dict[str, Any] = field(default_factory=lambda: {'fg': 'yellow'})
    template_name: Dict[str, Any] = field(default_factory=lambda: {'fg': 'white', 'bold': True})
    template_description: Dict[str, Any] = field(default_factory=lambda: {'fg': 'blue'})
    template_content: Dict[str, Any] = field(default_factory=lambda: {'fg': 'magenta'})
    template_comment: Dict[str, Any] = field(default_factory=lambda: {'fg': 'bright_black'})
    template_value: Dict[str, Any] = field(default_factory=lambda: {'fg': 'white'})

    # used in diff command
    diff_label: Dict[str, Any] = field(default_factory=lambda: {'fg': 'yellow'})
    diff_added: Dict[str, Any] = field(default_factory=lambda: {'fg': 'green'})
    diff_removed: Dict[str, Any] = field(default_factory=lambda: {'fg': 'red'})
    diff_changed: Dict[str, Any] = field(default_factory=lambda: {'fg': 'magenta'})
    diff_unchanged: Dict[str, Any] = field(default_factory=lambda: {'fg': 'bright_black'})


    def style(self, text, tp=None, **kwargs):
        """
        Wrapper around click.style that applies theme styles.

        Args:
            text: The text to style
            tp: Theme parameter - the style name to look up
            **kwargs: Additional click.style() arguments that override theme settings
        """

        tps = vars(self)
        if tp is not None and tp in tps:
            kwargs = dict(tps[tp], **kwargs)
        return style(text, **kwargs)


    def secho(self, message=None, tp=None, **kwargs):
        """
        Wrapper around click.echo that applies theme styles.

        Args:
            message: The message to output
            tp: Theme parameter - the style name to look up
            **kwargs: Additional click.secho() arguments that override theme settings
        """

        return echo(self.style(message, tp, **kwargs))


class NoColorTheme(ColorTheme):

    def style(self, text, tp=None, **kwargs):
        """
        Wrapper around click.style that applies theme styles.
        """

        return text


NOCOLOR_THEME = NoColorTheme()
DEFAULT_THEME = ColorTheme()


def select_theme():
    """
    Select the theme to use for the CLI output. If NO_COLOR env var is set,
    use the NOCOLOR_THEME, otherwise use the DEFAULT_THEME.
    """

    if os.environ.get('NO_COLOR', None):
        return NOCOLOR_THEME
    return DEFAULT_THEME


# The end.

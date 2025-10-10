"""
koji_habitude.cli.theme

Color theme system for CLI output.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 4.5 Sonnet via Cursor
"""

# Vibe-Coding State: AI Generated, Human Rework


from click import style, secho, echo
import os


__all__ = (
    'ColorTheme',
    'NoColorTheme',

    'DEFAULT_THEME',
    'NOCOLOR_THEME',

    'select_theme',
)


class ColorTheme:

    def __init__(self, **kwargs):
        self.styles = kwargs


    def style(self, text, tp=None, **kwargs):
        """
        Wrapper around click.style that applies theme styles.

        Args:
            text: The text to style
            tp: Theme parameter - the style name to look up
            **kwargs: Additional click.style() arguments that override theme settings
        """

        if tp is not None and tp in self.styles:
            # Merge theme styles with any explicit kwargs, preferring kwargs
            style_args = {**self.styles[tp], **kwargs}
            return style(text, **style_args)

        return style(text, **kwargs)


    def secho(self, message=None, tp=None, **kwargs):
        """
        Wrapper around click.secho that applies theme styles.

        Args:
            message: The message to output
            tp: Theme parameter - the style name to look up
            **kwargs: Additional click.secho() arguments that override theme settings
        """

        if tp is not None and tp in self.styles:
            # Merge theme styles with any explicit kwargs, preferring kwargs
            style_args = {**self.styles[tp], **kwargs}
            return secho(message, **style_args)

        return secho(message, **kwargs)


class NoColorTheme(ColorTheme):

    def style(self, text, tp=None, **kwargs):
        """
        Wrapper around click.style that applies theme styles.
        """

        return text

    def secho(self, message=None, tp=None, **kwargs):
        """
        Wrapper around click.secho that applies theme styles.
        """

        return echo(message, **kwargs)


NOCOLOR_THEME = NoColorTheme()

DEFAULT_THEME = ColorTheme(

    # used in display_summary and display_resolver_report
    type_heading={'fg': 'yellow'},
    object_name={'fg': 'white'},
    create={'fg': 'green'},
    update={'fg': 'cyan'},
    add={'fg': 'blue'},
    remove={'fg': 'red'},
    modify={'fg': 'magenta'},
    summary_text={'fg': 'bright_white'},
    unchanged_text={'fg': 'bright_black'},

    # used in template show
    template_label={'fg': 'yellow'},
    template_name={'fg': 'white', 'bold': True},
    template_description={'fg': 'blue'},
    template_content={'fg': 'magenta'},
    template_comment={'fg': 'bright_black'},
    template_value={'fg': 'white'},
)


def select_theme():
    """
    Select the theme to use for the CLI output.
    """

    if os.environ.get('NO_COLOR', None):
        return NOCOLOR_THEME
    return DEFAULT_THEME


# The end.

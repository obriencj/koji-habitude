"""
koji-habitude.cli.tests.test_cli_params

Tests for CLI command parameter introspection.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 4.5 Sonnet via Cursor
"""

from koji_habitude.cli import main
from . import assert_click_params_match_function


class TestCLIParams:
    """
    Test that CLI command parameters match their function signatures.
    """

    def test_apply_command_params(self):
        """
        Test that apply command params match its function signature.
        """

        cmd = main.get_command(None, 'apply')
        assert_click_params_match_function(cmd)


    def test_expand_command_params(self):
        """
        Test that expand command params match its function signature.
        """

        cmd = main.get_command(None, 'expand')
        assert_click_params_match_function(cmd)


    def test_compare_command_params(self):
        """
        Test that compare command params match its function signature.
        """

        cmd = main.get_command(None, 'compare')
        assert_click_params_match_function(cmd)


    def test_diff_command_params(self):
        """
        Test that diff command params match its function signature.
        """

        cmd = main.get_command(None, 'diff')
        assert_click_params_match_function(cmd)


    def test_fetch_command_params(self):
        """
        Test that fetch command params match its function signature.
        """

        cmd = main.get_command(None, 'fetch')
        assert_click_params_match_function(cmd)


    def test_dump_command_params(self):
        """
        Test that dump command params match its function signature.
        """

        cmd = main.get_command(None, 'dump')
        assert_click_params_match_function(cmd)


    def test_list_templates_command_params(self):
        """
        Test that list-templates command params match its function signature.
        """

        cmd = main.get_command(None, 'list-templates')
        assert_click_params_match_function(cmd)


    def test_template_subcommands(self):
        """
        Test that template subcommand params match their function signatures.
        """

        template_group = main.get_command(None, 'template')

        subcommands = ['show', 'expand', 'compare', 'diff', 'apply']
        for subcmd_name in subcommands:
            cmd = template_group.get_command(None, subcmd_name)
            assert_click_params_match_function(cmd)


# The end.

"""
koji-habitude.cli.tests

Test utilities for CLI command introspection.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 4.5 Sonnet via Cursor
"""

import inspect
import click


def get_command_function_params(cmd):
    """
    Extract the function signature parameters from a click Command.

    Args:
        cmd: A click.Command instance

    Returns:
        dict: Parameter name -> inspect.Parameter mapping
    """

    # Get the underlying function from the command
    func = cmd.callback

    # Get the signature
    sig = inspect.signature(func)

    return sig.parameters


def get_command_params(cmd):
    """
    Extract click parameters from a click Command.

    Args:
        cmd: A click.Command instance

    Returns:
        dict: Parameter name -> click.Parameter mapping
    """

    # Build a dict of name -> parameter
    params = {}
    for param in cmd.params:
        # Get the primary name (first one if multiple)
        name = param.name if hasattr(param, 'name') else param.opts[0] if param.opts else None
        if name:
            params[name] = param

    return params


def assert_click_params_match_function(cmd):
    """
    Assert that all click parameters match the underlying function signature.

    This checks:
    1. That all function parameters (except ctx, *args, **kwargs) have corresponding click params
    2. That all click params correspond to function parameters

    Args:
        cmd: A click.Command instance to validate

    Raises:
        AssertionError: If parameters don't match
    """

    func_params = get_command_function_params(cmd)
    click_params = get_command_params(cmd)

    # Check each function parameter
    for name, param in func_params.items():
        if name == 'ctx' or name.startswith('_'):
            # Skip context and internal parameters
            continue

        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            # Skip *args
            continue

        if param.kind == inspect.Parameter.VAR_KEYWORD:
            # Skip **kwargs
            continue

        # Check if there's a corresponding click parameter
        if name not in click_params:
            raise AssertionError(
                f"Function parameter '{name}' has no corresponding click option "
                f"in command '{cmd.name}'"
            )

    # Check each click parameter
    for name, param in click_params.items():
        if name not in func_params:
            raise AssertionError(
                f"Click parameter '{name}' has no corresponding function parameter "
                f"in command '{cmd.name}'"
            )


# The end.

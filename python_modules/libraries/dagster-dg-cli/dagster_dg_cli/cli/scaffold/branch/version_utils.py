"""Version-related utilities for scaffold branch command."""

import sys

import click


def ensure_claude_sdk_python_version() -> None:
    """Ensure Python version meets claude-code-sdk requirements.

    Raises:
        click.ClickException: If Python version is less than 3.10
    """
    if sys.version_info < (3, 10):
        raise click.ClickException(
            "The 'dg scaffold branch' command requires Python 3.10+ for claude-code-sdk support."
        )

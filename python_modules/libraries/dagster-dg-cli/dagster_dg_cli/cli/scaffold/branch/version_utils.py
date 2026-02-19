"""Version-related utilities for scaffold branch command."""


def ensure_claude_sdk_python_version() -> None:
    """Ensure Python version meets claude-code-sdk requirements.

    Raises:
        click.ClickException: If Python version is less than 3.10
    """

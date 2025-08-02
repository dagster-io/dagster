"""Git operations utilities for dagster-claude-commands."""

import subprocess
from typing import Optional

import click


def get_current_branch() -> Optional[str]:
    """Get the current git branch name."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"], capture_output=True, check=True, text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def get_commit_messages_since_ref(base_ref: str) -> str:
    """Get commit messages since the given reference."""
    try:
        result = subprocess.run(
            ["git", "log", f"{base_ref}..HEAD", "--oneline"],
            capture_output=True,
            check=True,
            text=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        click.echo(f"Error getting commit messages: {e}", err=True)
        return ""


def get_diff_since_ref(base_ref: str) -> str:
    """Get diff since the given reference."""
    try:
        result = subprocess.run(
            ["git", "diff", f"{base_ref}..HEAD"], capture_output=True, check=True, text=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        click.echo(f"Error getting diff: {e}", err=True)
        return ""


def amend_commit_message(message: str) -> bool:
    """Amend the current commit with a new message."""
    try:
        subprocess.run(["git", "commit", "--amend", "-m", message], capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        click.echo(f"Error amending commit: {e}", err=True)
        return False

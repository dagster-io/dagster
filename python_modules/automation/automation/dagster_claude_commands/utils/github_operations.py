"""GitHub CLI operations utilities for dagster-claude-commands."""

import json
import subprocess
from typing import Optional

import click


def update_pr_title_and_body(pr_url: str, title: str, body: str) -> bool:
    """Update PR title and body using GitHub CLI."""
    try:
        # Update title
        subprocess.run(
            ["gh", "pr", "edit", pr_url, "--title", title], capture_output=True, check=True
        )

        # Update body
        subprocess.run(
            ["gh", "pr", "edit", pr_url, "--body", body], capture_output=True, check=True
        )

        click.echo("✓ Updated PR title and body")
        return True

    except subprocess.CalledProcessError as e:
        click.echo(f"Error updating PR: {e}", err=True)
        return False


def get_current_pr_url() -> Optional[str]:
    """Get the PR URL for the current branch if it exists."""
    try:
        result = subprocess.run(
            ["gh", "pr", "view", "--json", "url"], capture_output=True, check=True, text=True
        )

        # Parse JSON output to get URL
        data = json.loads(result.stdout)
        return data.get("url")

    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return None

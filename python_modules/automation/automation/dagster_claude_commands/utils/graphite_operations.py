"""Graphite CLI operations utilities for dagster-claude-commands."""

import re
import subprocess
from typing import Optional

import click


def get_stack_base() -> Optional[str]:
    """Get the base reference for the current Graphite stack."""
    try:
        result = subprocess.run(["gt", "ls", "-s"], capture_output=True, check=True, text=True)
        lines = result.stdout.strip().split("\n")

        # Find the last branch in the stack (should be master/main)
        # or the branch before current one
        if len(lines) >= 2:
            # Return the last branch (typically master)
            last_line = lines[-1].strip()
            # Extract branch name from "◯  branch_name" format
            if last_line.startswith("◯"):
                return last_line.split(None, 1)[1] if len(last_line.split(None, 1)) > 1 else None

        return None
    except subprocess.CalledProcessError as e:
        click.echo(f"Error getting stack base: {e}", err=True)
        return None


def squash_branch() -> bool:
    """Squash all commits in the current branch."""
    try:
        subprocess.run(["gt", "squash", "--no-edit"], capture_output=True, check=True, text=True)
        click.echo("✓ Squashed commits successfully")
        return True
    except subprocess.CalledProcessError as e:
        # Check if there's nothing to squash
        if "nothing to squash" in str(e.stderr).lower():
            click.echo("i Branch has only one commit, nothing to squash")
            return True
        else:
            click.echo(f"Error squashing commits: {e}", err=True)
            return False


def submit_draft_pr() -> Optional[str]:
    """Submit a draft PR using Graphite and return the PR URL."""
    try:
        result = subprocess.run(
            ["gt", "submit", "-n", "-d"], capture_output=True, check=True, text=True
        )

        # Extract PR URL from output
        pr_url = extract_pr_url_from_output(result.stdout)
        if pr_url:
            click.echo(f"✓ Created/updated draft PR: {pr_url}")
            return pr_url
        else:
            click.echo("✓ Draft PR created/updated (URL not found in output)")
            return None

    except subprocess.CalledProcessError as e:
        click.echo(f"Error submitting draft PR: {e}", err=True)
        return None


def extract_pr_url_from_output(output: str) -> Optional[str]:
    """Extract GitHub PR URL from Graphite command output."""
    # Look for GitHub PR URLs in the output
    url_pattern = r"https://github\.com/[^/]+/[^/]+/pull/\d+"
    match = re.search(url_pattern, output)
    return match.group(0) if match else None

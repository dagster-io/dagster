"""Git integration utilities for branch deployment auto-detection."""

import re
import subprocess
from pathlib import Path
from typing import Optional

import click


def find_git_repo_root(start_path: Path) -> Path:
    """Walk up directory tree to find .git directory.

    Args:
        start_path: Starting directory path to search from

    Returns:
        Path to the git repository root

    Raises:
        click.UsageError: If no git repository is found
    """
    current = start_path.resolve()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent

    raise click.UsageError(
        f"No git repository found in {start_path} or parent directories. "
        "Branch deployment commands must be run from within a git repository."
    )


def get_local_repo_name(repo_root: Path) -> str:
    """Extract org/repo from git remote URL.

    Args:
        repo_root: Path to git repository root

    Returns:
        Repository name in format "org/repo"

    Raises:
        click.UsageError: If unable to determine repo name from git
    """
    try:
        repo_url = (
            subprocess.check_output(
                ["git", "config", "--get", "remote.origin.url"],
                cwd=repo_root,
                stderr=subprocess.PIPE,
            )
            .decode("utf-8")
            .strip()
        )

        # Handle both SSH URLs (git@github.com:org/repo.git)
        # and HTTPS URLs (https://github.com/org/repo.git)
        # Match the last two path segments before .git
        match = re.search(r"([^/:]+/[^/:]+?)(\.git)?$", repo_url)
        if match:
            return match.group(1)

        raise click.UsageError(f"Could not parse repository name from git remote URL: {repo_url}")

    except subprocess.CalledProcessError as e:
        raise click.UsageError(
            f"Could not determine repo name from git: {e}. "
            "Ensure you have a git remote named 'origin' configured."
        )


def get_local_branch_name(repo_root: Path) -> str:
    """Get current branch name.

    Args:
        repo_root: Path to git repository root

    Returns:
        Current branch name

    Raises:
        click.UsageError: If unable to determine branch name
    """
    try:
        branch = (
            subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_root,
                stderr=subprocess.PIPE,
            )
            .decode("utf-8")
            .strip()
        )

        if branch == "HEAD":
            raise click.UsageError(
                "Currently in detached HEAD state. "
                "Branch deployment requires being on a named branch."
            )

        return branch

    except subprocess.CalledProcessError as e:
        raise click.UsageError(
            f"Could not determine current branch from git: {e}. "
            "Ensure you are in a valid git repository with a checked-out branch."
        )


def read_git_commit_metadata(repo_root: Path) -> dict[str, str | float]:
    """Read commit metadata from git log.

    Uses git log to extract:
    - commit_hash: Full commit hash
    - author_email: Author email address
    - author_name: Author name
    - timestamp: Unix timestamp (float)
    - commit_message: Commit message

    Args:
        repo_root: Path to git repository root

    Returns:
        Dictionary containing commit metadata

    Raises:
        click.UsageError: If unable to read git state
    """
    # Format string for git log - extracts hash, email, name, timestamp, message
    # Separated by newlines
    format_string = "%H%n%ae%n%an%n%cd%n%s"

    try:
        output = subprocess.check_output(
            ["git", "log", "-1", f"--format={format_string}", "--date=unix"],
            cwd=repo_root,
            stderr=subprocess.PIPE,
        ).decode("utf-8")

        lines = output.strip().split("\n", 4)
        if len(lines) < 4:
            raise click.UsageError(
                "Could not read git commit metadata. "
                "Ensure you are in a git repository with at least one commit."
            )

        return {
            "commit_hash": lines[0],
            "author_email": lines[1],
            "author_name": lines[2],
            "timestamp": float(lines[3]),
            "commit_message": lines[4] if len(lines) > 4 else "",
        }

    except subprocess.CalledProcessError as e:
        raise click.UsageError(
            f"Could not read git state: {e}. "
            "Ensure you are in a valid git repository with at least one commit."
        )
    except (ValueError, IndexError) as e:
        raise click.UsageError(f"Error parsing git commit metadata: {e}")


def get_git_metadata_for_branch_deployment(
    start_path: Path, read_git_state: bool
) -> tuple[Path, str, str, Optional[dict[str, str | float]]]:
    """Get all git metadata needed for branch deployment.

    This is a convenience function that combines all git utilities.

    Args:
        start_path: Starting directory path to search from
        read_git_state: Whether to read commit metadata from git

    Returns:
        Tuple of (repo_root, repo_name, branch_name, commit_metadata)
        commit_metadata will be None if read_git_state is False

    Raises:
        click.UsageError: If unable to determine git metadata
    """
    repo_root = find_git_repo_root(start_path)
    repo_name = get_local_repo_name(repo_root)
    branch_name = get_local_branch_name(repo_root)

    commit_metadata = None
    if read_git_state:
        commit_metadata = read_git_commit_metadata(repo_root)

    return repo_root, repo_name, branch_name, commit_metadata

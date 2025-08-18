"""Git and GitHub operations for scaffold branch command."""

import os
import subprocess
from pathlib import Path
from typing import Optional

import click
from dagster_dg_core.version import __version__ as dg_version

from dagster_dg_cli.cli.scaffold.branch.ui import create_status_message


def get_dg_version() -> str:
    """Get the current dg version, using git commit hash for development versions."""
    if dg_version == "1!0+dev":
        dagster_repo = os.getenv("DAGSTER_GIT_REPO_DIR")
        if dagster_repo:
            result = run_git_command(["rev-parse", "HEAD"], cwd=Path(dagster_repo))
            return result.stdout.strip()

    return dg_version


def run_git_command(
    args: list[str], cwd: Optional[Path] = None
) -> subprocess.CompletedProcess[str]:
    """Run a git command and return the result.

    Args:
        args: List of git command arguments (without 'git' prefix)
        cwd: Working directory for the command

    Returns:
        subprocess.CompletedProcess result

    Raises:
        click.ClickException: If git is not found or command fails
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            check=True,
            cwd=cwd,
        )
        return result
    except FileNotFoundError:
        raise click.ClickException(
            "git command not found. Please ensure git is installed and available in PATH."
        )
    except subprocess.CalledProcessError as e:
        raise click.ClickException(f"git command failed: {e.stderr.strip() or e.stdout.strip()}")


def check_git_repository() -> None:
    """Check if the current directory is within a git repository.

    Raises:
        click.ClickException: If not in a git repository with instructions on how to fix it
    """
    try:
        run_git_command(["rev-parse", "--git-dir"])
    except click.ClickException as e:
        if "not a git repository" in str(e).lower():
            raise click.ClickException(
                "This command must be run within a git repository.\n"
                "To initialize a new git repository, run:\n"
                "  git init"
            )
        # Re-raise other git-related errors
        raise


def run_gh_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a gh (GitHub CLI) command and return the result.

    Args:
        args: List of gh command arguments (without 'gh' prefix)

    Returns:
        subprocess.CompletedProcess result

    Raises:
        click.ClickException: If gh is not found or command fails
    """
    try:
        result = subprocess.run(["gh"] + args, capture_output=True, text=True, check=True)
        return result
    except FileNotFoundError:
        raise click.ClickException(
            "gh command not found. Please ensure GitHub CLI is installed and available in PATH."
        )
    except subprocess.CalledProcessError as e:
        raise click.ClickException(f"gh command failed: {e.stderr.strip() or e.stdout.strip()}")


def create_git_branch(branch_name: str, event_emitter) -> str:
    """Create and checkout a new git branch.

    Args:
        branch_name: Name of the branch to create
        event_emitter: Callback function to emit status messages

    Returns:
        The commit hash of the new branch

    Raises:
        click.ClickException: If git operations fail
    """
    run_git_command(["checkout", "-b", branch_name])
    
    event_emitter(create_status_message("info", f"Created and checked out new branch: {branch_name}"))
    
    return run_git_command(["rev-parse", "HEAD"]).stdout.strip()


def create_empty_commit(message: str, event_emitter) -> None:
    """Create an empty git commit.

    Args:
        message: Commit message
        event_emitter: Callback function to emit status messages

    Raises:
        click.ClickException: If git operations fail
    """
    run_git_command(["commit", "--allow-empty", "-m", message])
    
    event_emitter(create_status_message("info", f"Created empty commit: {message}"))


def create_content_commit_and_push(message: str, local_only: bool = False) -> str:
    """Create a commit with current changes and optionally push to remote.

    Args:
        message: Commit message
        local_only: If True, don't push to remote

    Returns:
        The commit hash of the created commit

    Raises:
        click.ClickException: If git operations fail
    """
    run_git_command(["add", "-A"])
    run_git_command(["commit", "-m", message])
    if not local_only and has_remote_origin():
        run_git_command(["push"])
    return run_git_command(["rev-parse", "HEAD"]).stdout.strip()


def has_remote_origin() -> bool:
    """Check if the repository has a remote named 'origin'."""
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"], capture_output=True, text=True, check=False
    )
    return result.returncode == 0 and bool(result.stdout.strip())


def create_branch_and_pr(
    branch_name: str, pr_title: str, pr_body: str, event_emitter, local_only: bool = False
) -> str:
    """Push the current branch to remote and create a GitHub pull request.

    Args:
        branch_name: Name of the branch to push
        pr_title: Title of the pull request
        pr_body: Body/description of the pull request
        local_only: If True, skip pushing to remote and creating PR
        event_emitter: Callback function to emit status messages

    Returns:
        URL of the created pull request, or empty string if local_only

    Raises:
        click.ClickException: If git or gh operations fail
    """
    if local_only or not has_remote_origin():
        message = f"Branch {branch_name} created locally (no remote push)"
        event_emitter(create_status_message("info", message))
        return ""

    # Push the branch to remote
    run_git_command(["push", "-u", "origin", branch_name])
    push_message = f"Pushed branch {branch_name} to remote"
    event_emitter(create_status_message("info", push_message))

    # Create the pull request
    result = run_gh_command(["pr", "create", "--title", pr_title, "--body", pr_body])

    pr_url = result.stdout.strip()
    pr_message = f"Created pull request: {pr_url}"
    event_emitter(create_status_message("success", pr_message))
    
    return pr_url

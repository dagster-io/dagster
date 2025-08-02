"""Validation utilities for dagster-claude-commands."""

import subprocess
import sys
from typing import Optional

import click


def check_tool_available(tool_name: str) -> bool:
    """Check if external CLI tool is available."""
    try:
        subprocess.run([tool_name, "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def validate_git_repository() -> bool:
    """Check if current directory is a git repository."""
    try:
        subprocess.run(["git", "rev-parse", "--git-dir"], capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def get_current_branch() -> Optional[str]:
    """Get the current git branch name."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"], capture_output=True, check=True, text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def is_protected_branch(branch: str) -> bool:
    """Check if branch is protected (master/main)."""
    return branch.lower() in {"master", "main"}


def validate_prerequisites() -> None:
    """Validate all prerequisites for submit-summarized-pr command."""
    errors: list[str] = []

    # Check git repository
    if not validate_git_repository():
        errors.append("Must be run from within a git repository")

    # Check required CLI tools
    required_tools = ["git", "gt", "gh"]
    for tool in required_tools:
        if not check_tool_available(tool):
            tool_messages = {
                "gt": "Graphite CLI (gt) is required but not installed. Install from https://graphite.dev/",
                "gh": "GitHub CLI (gh) is required but not installed. Install from https://cli.github.com/",
                "git": "Git is required but not available",
            }
            errors.append(tool_messages.get(tool, f"{tool} is required but not installed"))

    # Check current branch
    current_branch = get_current_branch()
    if not current_branch:
        errors.append("Could not determine current git branch")
    elif is_protected_branch(current_branch):
        errors.append(
            f"Cannot run on protected branch '{current_branch}'. Switch to a feature branch first."
        )

    # Check if branch is part of Graphite stack
    try:
        result = subprocess.run(["gt", "ls", "-s"], capture_output=True, check=True, text=True)
        lines = result.stdout.strip().split("\n")
        if len(lines) < 2:
            errors.append("Current branch must be part of a Graphite stack. Run 'gt stack' first.")
    except subprocess.CalledProcessError:
        errors.append("Could not verify Graphite stack status. Ensure branch is part of a stack.")

    if errors:
        for error in errors:
            click.echo(f"Error: {error}", err=True)
        sys.exit(1)


def check_has_commits_to_squash() -> bool:
    """Check if branch has multiple commits that can be squashed."""
    try:
        # Get base of stack using same logic as graphite_operations
        result = subprocess.run(["gt", "ls", "-s"], capture_output=True, check=True, text=True)
        lines = result.stdout.strip().split("\n")

        if len(lines) < 2:
            return False

        # Get the last branch (base branch)
        last_line = lines[-1].strip()
        if last_line.startswith("◯"):
            stack_base = last_line.split(None, 1)[1] if len(last_line.split(None, 1)) > 1 else None
        else:
            return False

        if not stack_base:
            return False

        # Count commits since base
        result = subprocess.run(
            ["git", "rev-list", "--count", f"{stack_base}..HEAD"],
            capture_output=True,
            check=True,
            text=True,
        )
        commit_count = int(result.stdout.strip())
        return commit_count > 1

    except (subprocess.CalledProcessError, ValueError):
        return False

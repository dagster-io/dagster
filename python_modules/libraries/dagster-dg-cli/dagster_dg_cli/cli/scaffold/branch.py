import asyncio
import json
import subprocess
import textwrap
from pathlib import Path
from typing import Optional

import click
from claude_code_sdk import ClaudeCodeOptions, ResultMessage, query
from dagster_dg_core.config import normalize_cli_config
from dagster_dg_core.context import DgContext
from dagster_dg_core.shared_options import dg_global_options, dg_path_options
from dagster_dg_core.utils import DgClickCommand
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper


def _run_git_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a git command and return the result.

    Args:
        args: List of git command arguments (without 'git' prefix)

    Returns:
        subprocess.CompletedProcess result

    Raises:
        click.ClickException: If git is not found or command fails
    """
    try:
        result = subprocess.run(["git"] + args, capture_output=True, text=True, check=True)
        return result
    except FileNotFoundError:
        raise click.ClickException(
            "git command not found. Please ensure git is installed and available in PATH."
        )
    except subprocess.CalledProcessError as e:
        raise click.ClickException(f"git command failed: {e.stderr.strip() or e.stdout.strip()}")


def _run_gh_command(args: list[str]) -> subprocess.CompletedProcess[str]:
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


def create_git_branch(branch_name: str) -> None:
    """Create and checkout a new git branch.

    Args:
        branch_name: Name of the branch to create

    Raises:
        click.ClickException: If git operations fail
    """
    _run_git_command(["checkout", "-b", branch_name])
    click.echo(f"Created and checked out new branch: {branch_name}")


def create_empty_commit(message: str) -> None:
    """Create an empty git commit.

    Args:
        message: Commit message

    Raises:
        click.ClickException: If git operations fail
    """
    _run_git_command(["commit", "--allow-empty", "-m", message])
    click.echo(f"Created empty commit: {message}")


def push_branch_and_create_pr(branch_name: str, pr_title: str, pr_body: str) -> str:
    """Push the current branch to remote and create a GitHub pull request.

    Args:
        branch_name: Name of the branch to push
        pr_title: Title of the pull request
        pr_body: Body/description of the pull request

    Returns:
        URL of the created pull request

    Raises:
        click.ClickException: If git or gh operations fail
    """
    # Push the branch to remote
    _run_git_command(["push", "-u", "origin", branch_name])
    click.echo(f"Pushed branch {branch_name} to remote")

    # Create the pull request
    result = _run_gh_command(["pr", "create", "--title", pr_title, "--body", pr_body])

    pr_url = result.stdout.strip()
    click.echo(f"Created pull request: {pr_url}")
    return pr_url


def _branch_name_prompt(prompt: str) -> str:
    return textwrap.dedent(
        f"""
    You are a helpful assistant that creates a reasonable, valid git branch name and pull request title based on the user's stated goal.
    Respond only with the following JSON, nothing else. No leading or trailing backticks or markdown.
    {{
        "branch-name": "<branch-name>",
        "pr-title": "<pr-title>"
    }}

    The user's stated goal is: {prompt}.
    """
    )


async def get_branch_name_and_pr_title_from_prompt(
    dg_context: DgContext, prompt: str
) -> tuple[str, str]:
    """Invokes Claude under the hood to generate a reasonable, valid
    git branch name and pull request title based on the user's stated goal.
    """
    options = ClaudeCodeOptions(
        cwd=dg_context.root_path,
    )

    async for message in query(prompt=_branch_name_prompt(prompt), options=options):
        if isinstance(message, ResultMessage) and message.result:
            result = json.loads(message.result)
            return result["branch-name"], result["pr-title"]

    raise Exception("No result message found")


@click.command(name="branch", cls=DgClickCommand, hidden=True)
@click.argument("branch-name", type=str, required=False)
@dg_path_options
@dg_global_options
@cli_telemetry_wrapper
def scaffold_branch_command(
    branch_name: Optional[str], target_path: Path, **other_options: object
) -> None:
    """Scaffold a new branch."""
    cli_config = normalize_cli_config(other_options, click.get_current_context())
    dg_context = DgContext.for_workspace_or_project_environment(target_path, cli_config)

    # If no branch name provided, prompt for it
    if not branch_name:
        initial_task = click.prompt("What would you like to accomplish?")
        branch_name, pr_title = asyncio.run(
            get_branch_name_and_pr_title_from_prompt(dg_context, initial_task)
        )

    else:
        branch_name = branch_name.strip()
        pr_title = branch_name

    click.echo(f"Creating new branch: {branch_name}")

    # Create and checkout the new branch
    create_git_branch(branch_name)

    # Create an empty commit to enable PR creation
    commit_message = f"Initial commit for {branch_name} branch"
    create_empty_commit(commit_message)

    # Create PR with branch name as title and standard body
    pr_body = f"This pull request was generated by the Dagster `dg` CLI for branch '{branch_name}'."

    # Push branch and create PR
    pr_url = push_branch_and_create_pr(branch_name, pr_title, pr_body)

    click.echo(f"✅ Successfully created branch and pull request: {pr_url}")

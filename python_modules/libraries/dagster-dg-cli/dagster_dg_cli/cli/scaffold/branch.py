import functools
import json
import os
import re
import subprocess
import textwrap
from abc import ABC
from pathlib import Path
from typing import Optional

import click
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

    {prompt}.
    """
    )


@functools.cache
def _find_claude(dg_context: DgContext) -> Optional[list[str]]:
    try:  # on PATH
        subprocess.run(
            ["claude", "--version"],
            check=False,
            capture_output=True,
        )
        return ["claude"]
    except FileNotFoundError:
        pass

    try:  # check for alias (auto-updating version recommends registering an alias instead of putting on PATH)
        result = subprocess.run(
            [os.getenv("SHELL", "bash"), "-ic", "type claude"],
            capture_output=True,
            text=True,
            check=False,
        )
        path_match = re.search(r"(/[^\s`\']+)", result.stdout)
        if path_match:
            return [path_match.group(1)]
    except FileNotFoundError:
        pass

    return None


MAX_TURNS = 20


def _run_claude(
    dg_context: DgContext,
    prompt: str,
    allowed_tools: list[str],
    max_turns=MAX_TURNS,
    output_format="text",
) -> str:
    """Runs Claude with the given prompt and allowed tools."""
    claude_cmd = _find_claude(dg_context)
    assert claude_cmd is not None
    cmd = [
        *claude_cmd,
        "-p",
        prompt,
        "--allowedTools",
        ",".join(allowed_tools),
        "--maxTurns",
        str(max_turns),
        "--outputFormat",
        output_format,
    ]
    output = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
    )
    return output.stdout


class InputType(ABC):
    """Abstract base class for input types."""

    @classmethod
    def matches(cls, user_input: str) -> bool:
        """Whether the user input matches this input type."""
        raise NotImplementedError

    @classmethod
    def get_context(cls, user_input: str) -> str:
        """Fetches context from the user input, to be passed to AI tools."""
        raise NotImplementedError

    @classmethod
    def additional_allowed_tools(cls) -> list[str]:
        """Additional allowed tools to be passed to AI tools."""
        return []


def get_branch_name_and_pr_title_from_prompt(
    dg_context: DgContext, user_input: str, input_type: type[InputType]
) -> tuple[str, str]:
    """Invokes Claude under the hood to generate a reasonable, valid
    git branch name and pull request title based on the user's stated goal.
    """
    output = _run_claude(
        dg_context,
        _branch_name_prompt(input_type.get_context(user_input)),
        input_type.additional_allowed_tools(),
        output_format="text",
    )
    json_output = json.loads(output.strip())
    return json_output["branch-name"], json_output["pr-title"]


class TextInputType(InputType):
    """Passes along user input as-is."""

    @classmethod
    def matches(cls, user_input: str) -> bool:
        return True

    @classmethod
    def get_context(cls, user_input: str) -> str:
        return f"The user's stated goal is: {user_input}."

    @classmethod
    def additional_allowed_tools(cls) -> list[str]:
        return []


class GithubIssueInputType(InputType):
    """Matches GitHub issue URLs and instructs AI tools to fetch issue details."""

    @classmethod
    def matches(cls, user_input: str) -> bool:
        return user_input.startswith("https://github.com/")

    @classmethod
    def get_context(cls, user_input: str) -> str:
        return (
            "The user would like to create a branch to address the following "
            f"GitHub issue, which might describe a bug or a feature request: {user_input}."
            "Use the `gh issue view --repo OWNER/REPO` tool to fetch the issue details."
        )

    @classmethod
    def additional_allowed_tools(cls) -> list[str]:
        return ["Bash(gh issue view:*)"]


INPUT_TYPES = [GithubIssueInputType]


def _is_prompt_valid_git_branch_name(prompt: str) -> bool:
    """Whether the prompt is a valid git branch name."""
    return re.match(r"^[a-zA-Z0-9_.-]+$", prompt) is not None


@click.command(name="branch", cls=DgClickCommand, hidden=True)
@click.argument("prompt", type=str, nargs=-1)
@dg_path_options
@dg_global_options
@cli_telemetry_wrapper
def scaffold_branch_command(
    prompt: tuple[str, ...], target_path: Path, **other_options: object
) -> None:
    """Scaffold a new branch."""
    cli_config = normalize_cli_config(other_options, click.get_current_context())
    dg_context = DgContext.for_workspace_or_project_environment(target_path, cli_config)

    prompt_text = " ".join(prompt)

    # If the user input a valid git branch name, bypass AI inference and create the branch directly.
    if prompt_text and _is_prompt_valid_git_branch_name(prompt_text.strip()):
        branch_name = prompt_text.strip()
        pr_title = branch_name
    else:
        # Otherwise, use AI to infer the branch name and PR title. Try to match the input to a known
        # input type so we can gather more context.
        if not prompt_text:
            prompt_text = click.prompt("What would you like to accomplish?")
        assert prompt_text
        input_type = next(
            (input_type for input_type in INPUT_TYPES if input_type.matches(prompt_text)),
            TextInputType,
        )

        branch_name, pr_title = get_branch_name_and_pr_title_from_prompt(
            dg_context, prompt_text, input_type
        )

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

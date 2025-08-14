import json
import os
import re
import subprocess
import textwrap
import uuid
from abc import ABC
from contextlib import nullcontext
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import click
from dagster_dg_core.config import normalize_cli_config
from dagster_dg_core.context import DgContext
from dagster_dg_core.shared_options import dg_global_options, dg_path_options
from dagster_dg_core.utils import DgClickCommand
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_dg_core.version import __version__ as dg_version
from dagster_shared.record import as_dict, record

from dagster_dg_cli.utils.claude_utils import run_claude, run_claude_stream
from dagster_dg_cli.utils.ui import daggy_spinner_context


def _get_dg_version() -> str:
    if dg_version == "1!0+dev":
        dagster_repo = os.getenv("DAGSTER_GIT_REPO_DIR")
        if dagster_repo:
            result = _run_git_command(["rev-parse", "HEAD"], cwd=Path(dagster_repo))
            return result.stdout.strip()

    return dg_version


def _run_git_command(
    args: list[str], cwd: Optional[Path] = None
) -> subprocess.CompletedProcess[str]:
    """Run a git command and return the result.

    Args:
        args: List of git command arguments (without 'git' prefix)

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


def create_git_branch(branch_name: str) -> str:
    """Create and checkout a new git branch.

    Args:
        branch_name: Name of the branch to create

    Returns:
        The commit hash of the new branch

    Raises:
        click.ClickException: If git operations fail
    """
    _run_git_command(["checkout", "-b", branch_name])
    click.echo(f"Created and checked out new branch: {branch_name}")
    return _run_git_command(["rev-parse", "HEAD"]).stdout.strip()


def create_empty_commit(message: str) -> None:
    """Create an empty git commit.

    Args:
        message: Commit message

    Raises:
        click.ClickException: If git operations fail
    """
    _run_git_command(["commit", "--allow-empty", "-m", message])
    click.echo(f"Created empty commit: {message}")


def create_content_commit_and_push(message: str) -> str:
    _run_git_command(["add", "-A"])
    _run_git_command(["commit", "-m", message])
    _run_git_command(["push"])
    return _run_git_command(["rev-parse", "HEAD"]).stdout.strip()


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


def _scaffolding_prompt(user_input: str) -> str:
    return (Path(__file__).parent / "scaffold_prompt.md").read_text() + "\n" + user_input


def _allowed_commands_scaffolding() -> list[str]:
    return [
        "Bash(dg scaffold defs:*)",
        "Bash(dg list defs:*)",
        "Bash(dg list components:*)",
        "Bash(dg docs component:*)",
        "Bash(dg check yaml:*)",
        "Bash(dg check defs:*)",
        "Bash(dg list env:*)",
        "Bash(dg utils inspect-component:*)",
        "Bash(dg docs integrations:*)",
        "Bash(uv add:*)",
        "Bash(uv sync:*)",
        # update yaml files
        "Edit(**/*defs.yaml)",
        "Replace(**/*defs.yaml)",
        "Update(**/*defs.yaml)",
        "Write(**/*defs.yaml)",
        "Edit(**/*NEXT_STEPS.md)",
        "Replace(**/*NEXT_STEPS.md)",
        "Update(**/*NEXT_STEPS.md)",
        "Write(**/*NEXT_STEPS.md)",
        "Bash(touch:*)",
    ]


MAX_TURNS = 20


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
    output = run_claude(
        dg_context,
        _branch_name_prompt(input_type.get_context(user_input)),
        input_type.additional_allowed_tools(),
    )
    json_output = json.loads(output.strip())
    return json_output["branch-name"], json_output["pr-title"]


class PrintOutputChannel:
    def write(self, text: str) -> None:
        click.echo(text)


def scaffold_content_for_prompt(
    dg_context: DgContext, user_input: str, input_type: type[InputType], use_spinner: bool = True
) -> None:
    """Scaffolds content for the user's prompt."""
    spinner_ctx = (
        daggy_spinner_context("Scaffolding")
        if use_spinner
        else nullcontext(enter_result=PrintOutputChannel())
    )
    with spinner_ctx as spinner:
        run_claude_stream(
            dg_context,
            _scaffolding_prompt(input_type.get_context(user_input)),
            _allowed_commands_scaffolding() + input_type.additional_allowed_tools(),
            output_channel=spinner,
        )


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


@click.command(name="branch", cls=DgClickCommand, unlaunched=True)
@click.argument("prompt", type=str, nargs=-1)
@click.option("--disable-progress", is_flag=True, help="Disable progress spinner")
@click.option(
    "--record",
    type=Path,
    help="Directory to write out session information for later analysis.",
)
@dg_path_options
@dg_global_options
@cli_telemetry_wrapper
def scaffold_branch_command(
    prompt: tuple[str, ...],
    target_path: Path,
    disable_progress: bool,
    record: Optional[Path],
    **other_options: object,
) -> None:
    """Scaffold a new branch."""
    cli_config = normalize_cli_config(other_options, click.get_current_context())
    dg_context = DgContext.for_workspace_or_project_environment(target_path, cli_config)

    ai_scaffolding = False
    input_type = None

    if record and (not record.exists() or not record.is_dir()):
        raise click.UsageError(f"{record} is not an existing directory")

    prompt_text = " ".join(prompt)
    generated_outputs = {}
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

        spinner_ctx = (
            daggy_spinner_context("Generating branch name and PR title")
            if not disable_progress
            else nullcontext()
        )
        with spinner_ctx:
            branch_name, pr_title = get_branch_name_and_pr_title_from_prompt(
                dg_context, prompt_text, input_type
            )
        generated_outputs["branch_name"] = branch_name
        generated_outputs["pr_title"] = pr_title
        # For generated branch names, add a random suffix to avoid conflicts
        branch_name = branch_name + "-" + str(uuid.uuid4())[:8]
        ai_scaffolding = True

    click.echo(f"Creating new branch: {branch_name}")

    # Create and checkout the new branch
    branch_base_sha = create_git_branch(branch_name)

    # Create an empty commit to enable PR creation
    commit_message = f"Initial commit for {branch_name} branch"
    create_empty_commit(commit_message)

    # Create PR with branch name as title and standard body
    pr_body = f"This pull request was generated by the Dagster `dg` CLI for branch '{branch_name}'."

    # Push branch and create PR
    pr_url = push_branch_and_create_pr(branch_name, pr_title, pr_body)

    click.echo(f"✅ Successfully created branch and pull request: {pr_url}")

    first_pass_sha = None
    if ai_scaffolding and input_type:
        scaffold_content_for_prompt(
            dg_context, prompt_text, input_type, use_spinner=not disable_progress
        )
        first_pass_sha = create_content_commit_and_push(f"First pass at {branch_name}")

    if record:
        if first_pass_sha:
            generated_outputs["first_pass_commit"] = _run_git_command(
                ["git", "show", first_pass_sha]
            ).stdout.strip()

        session_data = Session(
            timestamp=datetime.now().isoformat(),
            dg_version=_get_dg_version(),
            branch_name=branch_name,
            pr_title=pr_title,
            pr_url=pr_url,
            branch_base_sha=branch_base_sha,
            first_pass_sha=first_pass_sha,
            input={
                "prompt": prompt_text,
            },
            output=generated_outputs,
        )
        record_path = record / f"{uuid.uuid4()}.json"
        record_path.write_text(json.dumps(as_dict(session_data), indent=2))
        click.echo(f"📝 Session recorded: {record_path}")


@record
class Session:
    """A recorded session of the `scaffold branch` command, useful for evaluating effectiveness."""

    # isoformat
    timestamp: str
    # what code was used - semver for published package, commit hash for local development
    dg_version: str
    # the name of the branch created (even if AI not used)
    branch_name: str
    # the title of the PR created (even if AI not used)
    pr_title: str
    # the URL of the PR created. Used to identify the target repo.
    pr_url: str
    # the commit hash of the branch base. Used to identify the state of the target repo.
    branch_base_sha: str
    # the commit hash of the generated first pass commit, if done.
    first_pass_sha: Optional[str]
    # collection of input information
    input: dict[str, Any]
    # collection of generated output
    output: dict[str, Any]

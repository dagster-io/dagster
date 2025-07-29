import os
import re
import subprocess
import textwrap
from pathlib import Path
from typing import Optional

import click
from dagster_dg_core.config import normalize_cli_config
from dagster_dg_core.context import DgContext
from dagster_dg_core.shared_options import dg_global_options, dg_path_options
from dagster_dg_core.utils import DgClickCommand, DgClickGroup
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


def _find_claude(dg_context: DgContext) -> Optional[list[str]]:
    try:  # on PATH
        subprocess.run(
            ["claude", "--version"],
            check=False,
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


def _context_prompt(dg_context: DgContext) -> str:
    return textwrap.dedent(
        f"""
        This session was started via the Dagster CLI `dg`. Your job is to complete the following steps, do not deviate from these steps:

        ## Steps

        1. Prompt the user for what they would like to accomplish.
        2. Create a reasonable, valid git branch name based on the user's stated goal. Call `dg scaffold utils create-branch <branch-name>` to create the branch.
           If the branch already exists, come up with a new branch name until it is unique.
        3. Create a pull request with a title based on the user's stated goal. The pull request body should match the following markdown:

        ```markdown
        ### This pull request was generated by the Dagster `dg scaffold branch` command.
        ```

        Call `dg scaffold utils create-pr <pr-title> <pr-body>` to create the pull request.
        4. Use `dg scaffold defs` commands to scaffold a set of Dagster definitions to get the user started on their goal. Select technologies appropriate
           for the user's goal. If you have a choice between multiple technologies, present them to the user and ask them to select the one they prefer.
           If no matching integrations are found, let the user know, and abort the session. Do not use commands outside of your list of allowed commands.
        5. Locate scaffolded YAML files and populaute them with data. Run `dg check yaml`, `dg check defs` to validate the files
           and `dg list defs` to see the definitions that were created.
        6. Update the newly generateddg list  `defs.yaml` file to mention all environment variables used across the scaffolded files. Do so with the format:
        ```yaml
        requirements:
          env:
            - <ENV_VAR_NAME>
            - <OTHER_ENV_VAR_NAME>
        ```
        Run the `dg list env` command to ensure all required environment variables are listed.
        7. Create a commit with a message explaining what you scaffolded. Call `dg scaffold utils create-commit <message>` to create the commit
            and push the branch to remote. You're done. Exit the session.

        ## Rules and context

        The following context will help you work with the user to accomplish their goals using the Dagster library and `dg` CLI.

        # Dagster

        Dagster is a data orchestration platform for building, testing, and monitoring data pipelines.

        # Definitions

        The Dagster library operates over definitions created by the user. The core definition types are:

        * Assets
        * Asset Checks
        * Jobs
        * Schedules
        * Sensors
        * Resources

        # Assets

        The primary Dagster definition type, representing a data object (table, file, model) that's produced by computation.
        Assets have the following identifying properties:
        * `key` - The unique identifier for the asset.
        * `group` - The group the asset belongs to.
        * `kind` - What type of asset it is (can be multiple kinds).
        * `tags` - User defined key value pairs.

        ## Asset Selection Syntax

        Assets can be selected using the following syntax:
        - key:"value" - exact key match
        - key:"prefix_*" - wildcard key matching
        - tag:"name" - exact tag match
        - tag:"name"="value" - tag with specific value
        - owner:"name" - filter by owner
        - group:"name" - filter by group
        - kind:"type" - filter by asset kind


        # Components
        An abstraction for creating Dagster Definitions.
        Component instances are most commonly defined in defs.yaml files. These files abide by the following required schema:

        ```yaml
        type: module.ComponentType # The Component type to instantiate
        attributes: ... # The attributes to pass to the Component. The Component type defines the schema of these attributes.
        ```
        Multiple component instances can be defined in a yaml file, separated by `---`.

        Component instances can also be defined in python files using the `@component_instance` decorator.

        # Project Layout

        The project root is `{dg_context.root_path}`.
        The defs path is `{dg_context.defs_path}`. Dagster definitions are defined via yaml and py files in this directory.

        # `dg` Dagster CLI
        The `dg` CLI is a tool for managing Dagster projects and workspaces.

        ## Essential Commands

        ```bash
        # Validation
        dg check yaml # Validate yaml files according to their schema (fast)
        dg check defs # Validate definitions by loading them fully (slower)

        # Scaffolding
        dg scaffold defs <component type> <component path within defs folder> # Create an instance of a Component type. Available types found via `dg list components`.
        dg scaffold defs dagster.<asset|job|schedule|sensor> # Create a new definition of a given type.
        dg scaffold component <name> # Create a new custom Component type

        # Searching
        dg list defs # Show project definitions
        dg list defs --assets <asset selection> # Show selected asset definitions
        dg list component-tree # Show the component tree
        dg list components # Show available component types
        dg docs component <component type> # Show documentation for a component type
        ```
        * The `dg` CLI will be effective in accomplishing tasks. Use --help to better understand how to use commands.
        * Prefer `dg list defs` over searching the files system when looking for Dagster definitions.
        * Use the --json flag to get structured output.

        """
    )


def _allowed_commands() -> list[str]:
    return [
        "Bash(dg scaffold utils create-branch:*)",
        "Bash(dg scaffold utils create-pr:*)",
        "Bash(dg scaffold defs:*)",
        "Bash(dg list defs:*)",
        "Bash(dg list components:*)",
        "Bash(dg docs component:*)",
        "Bash(dg check yaml:*)",
        "Bash(dg check defs:*)",
        "Bash(dg list env:*)",
        "Bash(dg scaffold utils create-commit:*)",
        # update yaml files
        "Edit",
        "Replace",
        "Update",
    ]


@click.command(name="branch", cls=DgClickCommand)
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
        claude_cmd = _find_claude(dg_context)
        assert claude_cmd is not None
        cmd = [
            *claude_cmd,
            _context_prompt(dg_context),
            "--allowedTools",
            ",".join(_allowed_commands()),
        ]
        subprocess.run(
            cmd,
            check=False,
        )
        return

    else:
        branch_name = branch_name.strip()

        click.echo(f"Creating new branch: {branch_name}")

        # Create and checkout the new branch
        create_git_branch(branch_name)

        # Create an empty commit to enable PR creation
        commit_message = f"Initial commit for {branch_name} branch"
        create_empty_commit(commit_message)

        # Create PR with branch name as title and standard body
        pr_title = branch_name
        pr_body = (
            f"This pull request was generated by the Dagster `dg` CLI for branch '{branch_name}'."
        )

        # Push branch and create PR
        pr_url = push_branch_and_create_pr(branch_name, pr_title, pr_body)

        click.echo(f"✅ Successfully created branch and pull request: {pr_url}")


@click.group(name="utils", hidden=True, cls=DgClickGroup)
def utils_group():
    """Hidden utility commands."""
    pass


@utils_group.command(name="create-branch", cls=DgClickCommand)
@click.argument("branch-name", type=str)
@cli_telemetry_wrapper
def create_branch_command(branch_name: str) -> None:
    """Create a new branch."""
    click.echo(f"Creating new branch: {branch_name}")

    create_git_branch(branch_name)
    create_empty_commit(f"Initial commit for {branch_name} branch")


@utils_group.command(name="create-pr", cls=DgClickCommand)
@click.argument("pr-title", type=str)
@click.argument("pr-body", type=str)
@cli_telemetry_wrapper
def create_pr_command(pr_title: str, pr_body: str) -> None:
    """Create a new pull request."""
    click.echo(f"Creating new pull request: {pr_title}")

    # get current branch name
    branch_name = _run_git_command(["branch", "--show-current"]).stdout.strip()

    pr_url = push_branch_and_create_pr(branch_name, pr_title, pr_body)
    click.echo(f"Created pull request: {pr_url}")


@utils_group.command(name="create-commit", cls=DgClickCommand)
@click.argument("commit-message", type=str)
@cli_telemetry_wrapper
def create_commit_command(commit_message: str) -> None:
    """Create a new commit with the given message and push the branch."""
    click.echo(f"Creating new commit: {commit_message}")

    # Get current branch name
    branch_name = _run_git_command(["branch", "--show-current"]).stdout.strip()

    # Create commit
    _run_git_command(["add", "-A"])
    _run_git_command(["commit", "--allow-empty", "-m", commit_message])
    click.echo(f"Created commit with message: {commit_message}")

    # Push branch
    _run_git_command(["push", "-u", "origin", branch_name])
    click.echo(f"Pushed branch {branch_name} to remote")

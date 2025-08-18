"""Main scaffold branch command implementation."""

import json
import re
import uuid
from contextlib import nullcontext
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from dagster_dg_core.config import normalize_cli_config
from dagster_dg_core.context import DgContext
from dagster_dg_core.shared_options import dg_global_options, dg_path_options
from dagster_dg_core.utils import DgClickCommand
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.record import as_dict, replace

from dagster_dg_cli.cli.scaffold.branch.diagnostics import (
    VALID_DIAGNOSTICS_LEVELS,
    DiagnosticsLevel,
    create_claude_diagnostics_service,
)
from dagster_dg_cli.cli.scaffold.branch.git import (
    check_git_repository,
    create_branch_and_pr,
    create_content_commit_and_push,
    create_empty_commit,
    create_git_branch,
    get_dg_version,
    has_remote_origin,
    run_git_command,
)
from dagster_dg_cli.cli.scaffold.branch.models import Session
from dagster_dg_cli.utils.claude_utils import (
    get_claude_sdk_unavailable_message,
    is_claude_sdk_available,
)
from dagster_dg_cli.utils.ui import daggy_spinner_context


def is_prompt_valid_git_branch_name(prompt: str) -> bool:
    """Whether the prompt is a valid git branch name."""
    return re.match(r"^[a-zA-Z0-9_.-]+$", prompt) is not None


@click.command(name="branch", cls=DgClickCommand, unlaunched=True)
@click.argument("prompt", type=str, nargs=-1)
@click.option("--disable-progress", is_flag=True, help="Disable progress spinner")
@click.option(
    "--local-only",
    is_flag=True,
    help="Create branch locally without pushing to remote or creating PR",
)
@click.option(
    "--record",
    type=Path,
    help="Directory to write out session information for later analysis.",
)
@click.option(
    "--diagnostics-level",
    type=click.Choice(VALID_DIAGNOSTICS_LEVELS),
    default="off",
    help="Enable structured diagnostics logging at specified level (default: off).",
)
@click.option(
    "--diagnostics-dir",
    type=Path,
    help="Directory to write diagnostics files (default: <system temp directory>/dg/diagnostics).",
)
@dg_path_options
@dg_global_options
@cli_telemetry_wrapper
def scaffold_branch_command(
    prompt: tuple[str, ...],
    target_path: Path,
    disable_progress: bool,
    local_only: bool,
    record: Optional[Path],
    diagnostics_level: DiagnosticsLevel,
    diagnostics_dir: Optional[Path],
    **other_options: object,
) -> None:
    """Scaffold a new branch (requires Python 3.10+)."""
    import sys

    if sys.version_info < (3, 10):
        raise click.ClickException("dg scaffold branch requires Python 3.10 or higher")

    # Basic input validation
    prompt_text = " ".join(prompt).strip()
    if not prompt_text:
        raise click.UsageError("Prompt cannot be empty")

    # DiagnosticsLevel is already validated by click.Choice, so this check is redundant
    # but kept for explicit validation in case of programmatic usage
    # Create Claude diagnostics service instance
    diagnostics = create_claude_diagnostics_service(
        level=diagnostics_level,
        output_dir=diagnostics_dir,
    )

    # Inform user where diagnostics will be written if enabled
    if diagnostics_level != "off":
        click.echo(
            f"🔍 Diagnostics enabled at level '{diagnostics_level}' - streaming to: {diagnostics.output_file}"
        )

    try:
        diagnostics.info(
            "command_start",
            "Starting scaffold branch command",
            {
                "prompt": prompt_text,
                "target_path": str(target_path),
                "local_only": local_only,
                "diagnostics_level": diagnostics_level,
            },
        )

        # Check if we're in a git repository before proceeding
        with diagnostics.time_operation("git_repository_check", "validation"):
            check_git_repository()

        cli_config = normalize_cli_config(other_options, click.get_current_context())
        with diagnostics.time_operation("context_creation", "initialization"):
            dg_context = DgContext.for_workspace_or_project_environment(target_path, cli_config)

        ai_scaffolding = False
        input_type = None

        if record and (not record.exists() or not record.is_dir()):
            raise click.UsageError(f"{record} is not an existing directory")

        # prompt_text already defined above from validation
        generated_outputs = {}
        pr_title = ""  # Initialize pr_title

        # If the user input a valid git branch name, bypass AI inference and create the branch directly.
        if prompt_text and is_prompt_valid_git_branch_name(prompt_text.strip()):
            diagnostics.info(
                "branch_name_direct",
                "Using prompt as direct branch name",
                {"branch_name": prompt_text.strip()},
            )
            branch_name = prompt_text.strip()
            pr_title = branch_name
        else:
            # Check if Claude Code SDK is available before proceeding with AI operations
            if not is_claude_sdk_available():
                raise click.ClickException(get_claude_sdk_unavailable_message())

            # Import AI modules only when needed and available
            from dagster_dg_cli.cli.scaffold.branch.ai import (
                INPUT_TYPES,
                TextInputType,
                get_branch_name_and_pr_title_from_prompt,
                scaffold_content_for_prompt,
            )

            # Otherwise, use AI to infer the branch name and PR title. Try to match the input to a known
            # input type so we can gather more context.
            if not prompt_text:
                prompt_text = click.prompt("What would you like to accomplish?")
            assert prompt_text

            with diagnostics.time_operation("input_type_detection", "ai_preprocessing"):
                input_type = next(
                    (input_type for input_type in INPUT_TYPES if input_type.matches(prompt_text)),
                    TextInputType,
                )

            diagnostics.info(
                "input_type_detected",
                "Detected input type for prompt",
                {
                    "input_type": input_type.__name__,
                    "prompt_length": len(prompt_text),
                },
            )

            spinner_ctx = (
                daggy_spinner_context("Generating branch name and PR title")
                if not disable_progress
                else nullcontext()
            )
            with spinner_ctx:
                with diagnostics.time_operation("branch_name_generation", "ai_generation"):
                    branch_generation = get_branch_name_and_pr_title_from_prompt(
                        dg_context, prompt_text, input_type, diagnostics
                    )
            # Update final branch name with suffix to avoid conflicts
            final_branch_name = branch_generation.original_branch_name + "-" + str(uuid.uuid4())[:8]
            branch_generation = replace(branch_generation, final_branch_name=final_branch_name)

            generated_outputs["branch_name"] = branch_generation.original_branch_name
            generated_outputs["pr_title"] = branch_generation.pr_title
            branch_name = final_branch_name
            pr_title = branch_generation.pr_title
            ai_scaffolding = True

            diagnostics.info(
                "branch_name_generated",
                "Generated branch name and PR title",
                {
                    "original_branch_name": branch_generation.original_branch_name,
                    "final_branch_name": branch_generation.final_branch_name,
                    "pr_title": branch_generation.pr_title,
                },
            )

        click.echo(f"Creating new branch: {branch_name}")

        # Create and checkout the new branch
        with diagnostics.time_operation("git_branch_creation", "git_operations"):
            branch_base_sha = create_git_branch(branch_name)

        # Create an empty commit to enable PR creation
        commit_message = f"Initial commit for {branch_name} branch"
        with diagnostics.time_operation("empty_commit_creation", "git_operations"):
            create_empty_commit(commit_message)

        # Determine if we should work locally only
        effective_local_only = local_only or not has_remote_origin()

        diagnostics.info(
            "branch_mode",
            "Determined branch creation mode",
            {
                "local_only_flag": local_only,
                "has_remote": has_remote_origin(),
                "effective_local_only": effective_local_only,
            },
        )

        if effective_local_only:
            click.echo(f"✅ Successfully created branch: {branch_name}")
            pr_url = ""
        else:
            # Create PR with branch name as title and standard body
            pr_body = f"This pull request was generated by the Dagster `dg` CLI for branch '{branch_name}'."

            # Push branch and create PR
            with diagnostics.time_operation("pr_creation", "git_operations"):
                pr_url = create_branch_and_pr(branch_name, pr_title, pr_body, effective_local_only)

            click.echo(f"✅ Successfully created branch and pull request: {pr_url}")

        first_pass_sha = None
        if ai_scaffolding and input_type:
            # scaffold_content_for_prompt was imported above when AI was available
            with diagnostics.time_operation("content_scaffolding", "ai_generation"):
                scaffold_content_for_prompt(
                    prompt_text,
                    input_type,
                    diagnostics,
                    use_spinner=not disable_progress,
                )
            with diagnostics.time_operation("content_commit", "git_operations"):
                first_pass_sha = create_content_commit_and_push(
                    f"First pass at {branch_name}", effective_local_only
                )

        if record:
            if first_pass_sha:
                generated_outputs["first_pass_commit"] = run_git_command(
                    ["show", first_pass_sha]
                ).stdout.strip()

            session_data = Session(
                timestamp=datetime.now().isoformat(),
                dg_version=get_dg_version(),
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

            diagnostics.info(
                "session_recorded",
                "Session data recorded to file",
                {"record_path": str(record_path)},
            )

        diagnostics.info(
            "command_completed",
            "Scaffold branch command completed successfully",
            {
                "branch_name": branch_name,
                "pr_url": pr_url,
                "ai_scaffolding": ai_scaffolding,
                "first_pass_sha": first_pass_sha,
            },
        )

    except Exception as e:
        if diagnostics:
            diagnostics.error(
                "command_failed",
                "Scaffold branch command failed",
                {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
            )
        raise
    finally:
        # Always flush diagnostics on exit
        if diagnostics_level != "off":
            click.echo(f"🔍 Flushing diagnostics... Entries count: {len(diagnostics.entries)}")
        diagnostics_output = diagnostics.flush()
        if diagnostics_output and diagnostics_level != "off":
            click.echo(f"🔍 Diagnostics written to: {diagnostics_output}")
        elif diagnostics_level != "off":
            click.echo("🔍 No diagnostics file written (no entries or flush returned None)")

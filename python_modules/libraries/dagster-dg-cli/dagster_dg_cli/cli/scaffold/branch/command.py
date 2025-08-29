"""Main scaffold branch command implementation."""

import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from dagster_dg_core.config import normalize_cli_config
from dagster_dg_core.context import DgContext
from dagster_dg_core.shared_options import dg_global_options, dg_path_options
from dagster_dg_core.utils import DgClickCommand
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared.record import as_dict

from dagster_dg_cli.cli.scaffold.branch.ai import enter_waiting_phase
from dagster_dg_cli.cli.scaffold.branch.claude.diagnostics import (
    VALID_DIAGNOSTICS_LEVELS,
    DiagnosticsLevel,
    create_claude_diagnostics_service,
)

# Lazy import of ClaudeSDKClient to avoid docs build failures when claude_code_sdk is not available
from dagster_dg_cli.cli.scaffold.branch.constants import VALID_MODELS, ModelType
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
from dagster_dg_cli.cli.scaffold.branch.planning import (
    PlanGenerator,
    PlanningContext,
    get_user_plan_approval,
)
from dagster_dg_cli.cli.scaffold.branch.version_utils import ensure_claude_sdk_python_version
from dagster_dg_cli.utils.claude_utils import is_claude_sdk_available


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
@click.option(
    "--planning-model",
    type=click.Choice(list(VALID_MODELS)),
    default="opus",
    help="Model to use for planning phase (default: opus). Options: opus, sonnet, haiku.",
)
@click.option(
    "--execution-model",
    type=click.Choice(list(VALID_MODELS)),
    default="sonnet",
    help="Model to use for execution phase (default: sonnet). Options: opus, sonnet, haiku.",
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
    planning_model: ModelType,
    execution_model: ModelType,
    **other_options: object,
) -> None:
    """Scaffold a new branch (requires Python 3.10+)."""
    user_text = " ".join(prompt).strip()

    # DiagnosticsLevel is already validated by click.Choice, so this check is redundant
    # but kept for explicit validation in case of programmatic usage

    # Validate model selections
    if planning_model not in VALID_MODELS:
        raise click.UsageError(f"planning_model must be one of {VALID_MODELS}")
    if execution_model not in VALID_MODELS:
        raise click.UsageError(f"execution_model must be one of {VALID_MODELS}")

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
        with diagnostics.claude_operation(
            operation_name="scaffold_branch_command",
            error_code="command_failed",
            error_message="Scaffold branch command failed",
        ):
            execute_scaffold_branch_command(
                target_path,
                disable_progress,
                local_only,
                record,
                diagnostics_level,
                other_options,
                user_text,
                diagnostics,
                planning_model,
                execution_model,
            )
    except Exception as e:
        if diagnostics:
            diagnostics.error(
                category="command_failed",
                message="Scaffold branch command failed",
                data={
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


def execute_scaffold_branch_command(
    target_path,
    disable_progress,
    local_only,
    record,
    diagnostics_level,
    other_options,
    user_text,
    diagnostics,
    planning_model,
    execution_model,
):
    diagnostics.info(
        category="command_start",
        message="Starting scaffold branch command",
        data={
            "user_text": user_text,
            "target_path": str(target_path),
            "local_only": local_only,
            "diagnostics_level": diagnostics_level,
            "planning_model": planning_model,
            "execution_model": execution_model,
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
    current_plan = None
    prompt_text = None

    if record and (not record.exists() or not record.is_dir()):
        raise click.UsageError(f"{record} is not an existing directory")

    generated_outputs = {}
    pr_title = ""  # Initialize pr_title

    # If the user input a valid git branch name, bypass AI inference and create the branch directly.
    if user_text and is_prompt_valid_git_branch_name(user_text.strip()):
        diagnostics.info(
            category="branch_name_direct",
            message="Using prompt as direct branch name",
            data={"branch_name": user_text.strip()},
        )
        branch_name = user_text.strip()
        pr_title = branch_name
    else:
        # Check if Claude Code SDK and api key are available before proceeding with AI operations
        if not is_claude_sdk_available():
            raise click.ClickException(
                "claude_code_sdk is required for AI scaffolding functionality. "
                "Install with: pip install claude-code-sdk>=0.0.19"
            )

        # Import AI modules only when needed and available
        from dagster_dg_cli.cli.scaffold.branch.ai import (
            INPUT_TYPES,
            TextInputType,
            get_branch_name_and_pr_title_from_plan,
        )

        # Otherwise, use AI to infer the branch name and PR title. Try to match the input to a known
        # input type so we can gather more context.
        if not user_text:
            user_text = click.prompt("What would you like to accomplish?")
            if not user_text:
                raise click.UsageError("Prompt cannot be empty")

        with diagnostics.time_operation("input_type_detection", "ai_preprocessing"):
            input_type = next(
                (input_type for input_type in INPUT_TYPES if input_type.matches(user_text)),
                TextInputType,
            )
            prompt_text = input_type.get_context(user_text)

        diagnostics.info(
            category="input_type_detected",
            message="Detected input type for prompt",
            data={
                "input_type": input_type.__name__,
                "prompt_length": len(prompt_text),
            },
        )

        # Always start with planning phase
        with diagnostics.time_operation("planning_mode", "planning"):
            ensure_claude_sdk_python_version()

            from dagster_dg_cli.cli.scaffold.branch.claude.sdk_client import ClaudeSDKClient

            claude_client = ClaudeSDKClient(diagnostics)
            plan_generator = PlanGenerator(claude_client, diagnostics)

            # Create planning context
            planning_context = PlanningContext(
                model=planning_model,
                prompt_text=prompt_text,
                dg_context=dg_context,
                project_structure={
                    "root_path": str(dg_context.root_path),
                },
                verbose=cli_config.get("verbose", False),
            )

            # Generate initial plan
            click.echo("🎯 Generating implementation plan...")
            click.echo(f'📋 Request: "{prompt_text[:60]}{"..." if len(prompt_text) > 60 else ""}"')
            click.echo(
                f"🤖 Planning Model: {planning_model} (reasoning-focused for complex planning)"
            )
            click.echo(f"📁 Project: {dg_context.root_path}")

            with enter_waiting_phase(
                "Generating plan", spin=not disable_progress
            ) as output_channel:
                initial_plan = plan_generator.generate_initial_plan(
                    planning_context,
                    output_channel,
                )

            # Interactive plan review and refinement
            current_plan = initial_plan
            max_refinement_rounds = 3
            refinement_count = 0

            while refinement_count < max_refinement_rounds:
                approved, feedback = get_user_plan_approval(current_plan)

                if approved:
                    click.echo("✅ Plan approved! Proceeding with implementation...")
                    diagnostics.info(
                        category="plan_approved",
                        message="User approved the implementation plan",
                        data={
                            "plan_content_length": len(current_plan.markdown_content),
                            "refinement_rounds": refinement_count,
                        },
                    )
                    break  # Exit the planning loop and proceed to execution
                elif feedback:
                    # Refine the plan
                    click.echo("🔄 Refining plan based on your feedback...")
                    with enter_waiting_phase(
                        "Refining plan", spin=not disable_progress
                    ) as output_channel:
                        current_plan = plan_generator.refine_plan(
                            planning_context,
                            current_plan,
                            feedback,
                            output_channel,
                        )
                    refinement_count += 1
                else:
                    # User cancelled
                    return
            else:
                # Maximum refinement rounds reached
                click.echo("⚠️  Maximum refinement rounds reached. Final plan:")
                click.echo(current_plan.markdown_content)

                # Ask user if they want to proceed anyway
                if not click.confirm("Would you like to proceed with this plan?"):
                    return

        # Proceed with execution after plan approval
        click.echo("\n🚀 Beginning implementation...")

        click.echo("Extracting branch name and PR title")
        extracted = get_branch_name_and_pr_title_from_plan(
            current_plan.markdown_content,
            diagnostics,
        )

        # Update final branch name with suffix to avoid conflicts
        final_branch_name = extracted.branch_name + "-" + str(uuid.uuid4())[:8]

        generated_outputs["branch_name"] = extracted.branch_name
        generated_outputs["pr_title"] = extracted.pr_title
        branch_name = final_branch_name
        pr_title = extracted.pr_title
        ai_scaffolding = True

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
        category="branch_mode",
        message="Determined branch creation mode",
        data={
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
        pr_body = (
            f"This pull request was generated by the Dagster `dg` CLI for branch '{branch_name}'."
        )

        # Push branch and create PR
        with diagnostics.time_operation("pr_creation", "git_operations"):
            pr_url = create_branch_and_pr(branch_name, pr_title, pr_body, effective_local_only)

        click.echo(f"✅ Successfully created branch and pull request: {pr_url}")

    first_pass_sha = None
    if ai_scaffolding and current_plan and input_type:
        # Import scaffold_content_for_prompt only when we need it
        from dagster_dg_cli.cli.scaffold.branch.ai import scaffold_content_for_plan

        with diagnostics.time_operation("content_scaffolding", "ai_generation"):
            scaffold_content_for_plan(
                current_plan.markdown_content,
                input_type,
                diagnostics,
                verbose=cli_config.get("verbose", False),
                use_spinner=not disable_progress,
                model=execution_model,
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
            category="session_recorded",
            message="Session data recorded to file",
            data={"record_path": str(record_path)},
        )

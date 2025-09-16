"""AI interaction and input type handling for scaffold branch command."""

import asyncio
import re
from abc import ABC
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from time import perf_counter
from typing import TYPE_CHECKING

import click
from dagster_shared.record import record
from dagster_shared.utils.timing import format_duration

from dagster_dg_cli.cli.scaffold.branch.claude.diagnostics import ClaudeDiagnostics
from dagster_dg_cli.cli.scaffold.branch.constants import (
    ALLOWED_COMMANDS_PLANNING,
    ALLOWED_COMMANDS_SCAFFOLDING,
    ModelType,
)
from dagster_dg_cli.cli.scaffold.branch.version_utils import ensure_claude_sdk_python_version
from dagster_dg_cli.utils.ui import daggy_spinner_context

if TYPE_CHECKING:
    from dagster_dg_cli.cli.scaffold.branch.claude.sdk_client import OutputChannel


@record
class ExtractedNames:
    branch_name: str
    pr_title: str


def load_prompt_template(prompt_filename: str, context: str) -> str:
    """Load a prompt template and inject context.

    Args:
        prompt_filename: The name of the prompt file (e.g., 'branch_name_only.md')
        context: The context to inject into the prompt

    Returns:
        The formatted prompt string
    """
    prompt_path = Path(__file__).parent / "prompts" / prompt_filename
    template = prompt_path.read_text()
    return template.format(context=context)


def load_scaffolding_prompt(plan: str) -> str:
    """Load the scaffolding prompt template and append user input.

    Args:
        plan: The output of the planning phase

    Returns:
        The full scaffolding prompt
    """
    prompts_dir = Path(__file__).parent / "prompts"

    best_practices = (prompts_dir / "best_practices.md").read_text()
    return plan + "\n\n" + best_practices


def get_allowed_commands_scaffolding() -> list[str]:
    """Get the list of allowed commands for scaffolding operations."""
    return ALLOWED_COMMANDS_SCAFFOLDING.copy()


def get_allowed_commands_planning() -> list[str]:
    """Get the list of allowed commands for planning operations.

    Planning operations need to analyze the codebase but should not
    make any modifications. This returns a read-only subset of tools.
    """
    return ALLOWED_COMMANDS_PLANNING.copy()


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


def get_branch_name(plan: str, diagnostics: ClaudeDiagnostics) -> str:
    """Extract branch name from plan using regex based on planning_prompt.md format.

    Expected format: **Proposed Branch Name:** `branch-name`
    """
    match = re.search(r"\*\*Proposed Branch Name:\*\* `([^`]+)`", plan)
    if match:
        branch_name = match.group(1)
        diagnostics.info(
            category="branch_name_extracted",
            message="Successfully extracted branch name from plan",
            data={"branch_name": branch_name},
        )
        return branch_name

    diagnostics.error(
        category="branch_name_extraction_failed",
        message="Could not extract branch name from plan",
        data={"plan_snippet": plan[:200]},
    )
    raise click.ClickException("Could not extract branch name from plan")


def get_pr_title(plan: str, diagnostics: ClaudeDiagnostics) -> str:
    """Extract PR title from plan using regex based on planning_prompt.md format.

    Expected format: **Proposed PR Title:** "Title text"
    """
    match = re.search(r'\*\*Proposed PR Title:\*\* "([^"]+)"', plan)
    if match:
        pr_title = match.group(1)
        diagnostics.info(
            category="pr_title_extracted",
            message="Successfully extracted PR title from plan",
            data={"pr_title": pr_title},
        )
        return pr_title

    diagnostics.error(
        category="pr_title_extraction_failed",
        message="Could not extract PR title from plan",
        data={"plan_snippet": plan[:200]},
    )
    raise click.ClickException("Could not extract PR title from plan")


def get_branch_name_and_pr_title_from_plan(
    plan: str,
    diagnostics: ClaudeDiagnostics,
) -> ExtractedNames:
    """Extracts branch name and PR title from the plan using regex based on
    the format defined in planning_prompt.md.
    """
    diagnostics.info(
        category="branch_name_and_title_generation_start",
        message="Starting branch name and PR title generation",
        data={
            "context_length": len(plan),
        },
    )

    start_time = perf_counter()

    branch_name = get_branch_name(plan, diagnostics)
    pr_title = get_pr_title(plan, diagnostics)

    duration_ms = (perf_counter() - start_time) * 1000

    diagnostics.info(
        category="branch_name_and_title_generated",
        message="Successfully generated branch name and PR title",
        data={
            "branch_name": branch_name,
            "pr_title": pr_title,
            "duration_ms": duration_ms,
        },
    )

    return ExtractedNames(
        branch_name=branch_name,
        pr_title=pr_title,
    )


class PrintOutputChannel:
    """Output channel that prints to stdout using click.echo."""

    def write(self, text: str) -> None:
        click.echo(text)


@contextmanager
def enter_waiting_phase(phase_name: str, spin: bool = True) -> Iterator["OutputChannel"]:
    """Enter a phase of non interactivity where we wait for the CLI agent to complete its work.

    This yields an OutputChannel that coordinates with a loading indicator unless spin is disabled.
    """
    if spin:
        with daggy_spinner_context(phase_name) as spinner:
            yield spinner
    else:
        channel = PrintOutputChannel()
        channel.write(phase_name)
        yield channel


def scaffold_content_for_plan(
    plan: str,
    input_type: type[InputType],
    diagnostics: ClaudeDiagnostics,
    verbose: bool,
    model: ModelType,
    use_spinner: bool = True,
) -> None:
    """Scaffolds content from the plan generated by the planning phase."""
    ensure_claude_sdk_python_version()

    from claude_code_sdk.types import ResultMessage

    from dagster_dg_cli.cli.scaffold.branch.claude.sdk_client import ClaudeSDKClient

    prompt = load_scaffolding_prompt(plan)
    allowed_tools = get_allowed_commands_scaffolding() + input_type.additional_allowed_tools()

    with enter_waiting_phase("Scaffolding", spin=use_spinner) as channel:
        with diagnostics.claude_operation(
            operation_name="content_scaffolding",
            error_code="content_scaffolding_failed",
            error_message="Content scaffolding failed with SDK",
        ):
            claude_sdk = ClaudeSDKClient(diagnostics)

            messages = asyncio.run(
                claude_sdk.scaffold_with_streaming(
                    prompt=prompt,
                    model=model,
                    allowed_tools=allowed_tools,
                    output_channel=channel,
                    disallowed_tools=["Bash(python:*)", "WebSearch", "WebFetch"],
                    verbose=verbose,
                )
            )

    for message in messages:
        if isinstance(message, ResultMessage):
            click.echo(
                f"✅ Scaffolding completed (${message.total_cost_usd:.2f}, {format_duration(message.duration_ms)})."
            )

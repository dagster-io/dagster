"""AI interaction and input type handling for scaffold branch command."""

import asyncio
import os
from abc import ABC
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from time import perf_counter
from typing import Any

import click
from dagster_dg_core.context import DgContext
from dagster_shared.record import record

from dagster_dg_cli.cli.scaffold.branch.claude.diagnostics import ClaudeDiagnostics
from dagster_dg_cli.cli.scaffold.branch.claude.sdk_client import OutputChannel
from dagster_dg_cli.cli.scaffold.branch.constants import (
    ALLOWED_COMMANDS_PLANNING,
    ALLOWED_COMMANDS_SCAFFOLDING,
    ModelType,
)
from dagster_dg_cli.cli.scaffold.branch.version_utils import ensure_claude_sdk_python_version
from dagster_dg_cli.utils.ui import daggy_spinner_context


@record
class BranchNameGeneration:
    """Branch name generation result."""

    original_branch_name: str
    final_branch_name: str
    pr_title: str
    generation_metadata: dict[str, Any]


MAX_TURNS = 20


def invoke_anthropic_api_direct(
    prompt: str,
    diagnostics: ClaudeDiagnostics,
    operation_name: str,
) -> str:
    """Invoke Anthropic API directly to get a single string result.

    Args:
        prompt: The prompt to send to Claude
        diagnostics: Diagnostics service for logging
        operation_name: Name of the operation for logging

    Returns:
        Clean string result from Claude

    Raises:
        ValueError: If no valid string result can be extracted
    """
    # Get API key from environment
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is required for direct API calls")

    with diagnostics.claude_operation(
        operation_name=operation_name,
        error_code=f"{operation_name}_generation_failed",
        error_message=f"Failed to generate {operation_name} via Anthropic API",
        prompt_length=len(prompt),
    ):
        # Lazy import to avoid performance regression
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=100,  # Short responses for branch names/titles
            temperature=0.0,  # Deterministic output
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract text content from response
        if not response.content:
            raise ValueError(f"Empty response from Anthropic API for {operation_name}")

        # Get text from the first content block
        text_content = None
        for content_block in response.content:
            if content_block.type == "text":
                text_content = content_block.text
                break

        if not text_content:
            raise ValueError(f"No text content in Anthropic API response for {operation_name}")

        # Return the entire text content with newlines preserved
        result = text_content

        if not result.strip():
            raise ValueError(f"Empty {operation_name} returned from Anthropic API")

        return result


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


def get_branch_name(
    context: str,
    input_type: type["InputType"],
    diagnostics: ClaudeDiagnostics,
    model: ModelType = "sonnet",
) -> str:
    """Generate a git branch name from context.

    Args:
        context: The context to inject into the prompt
        input_type: The input type for additional allowed tools (unused in direct API mode)
        diagnostics: Diagnostics service for logging

    Returns:
        Generated branch name

    Raises:
        ValueError: If no valid branch name can be extracted
    """
    prompt = load_prompt_template("branch_name_only.md", context)
    return invoke_anthropic_api_direct(prompt, diagnostics, "branch_name")


def get_pr_title(
    context: str,
    input_type: type["InputType"],
    diagnostics: ClaudeDiagnostics,
    model: ModelType = "sonnet",
) -> str:
    """Generate a PR title from context.

    Args:
        context: The context to inject into the prompt
        input_type: The input type for additional allowed tools (unused in direct API mode)
        diagnostics: Diagnostics service for logging

    Returns:
        Generated PR title

    Raises:
        ValueError: If no valid PR title can be extracted
    """
    prompt = load_prompt_template("pr_title_only.md", context)
    return invoke_anthropic_api_direct(prompt, diagnostics, "pr_title")


def load_scaffolding_prompt(user_input: str) -> str:
    """Load the scaffolding prompt template and append user input.

    Args:
        user_input: The user's input to append to the prompt

    Returns:
        The full scaffolding prompt
    """
    prompts_dir = Path(__file__).parent / "prompts"

    # Load and concatenate the two prompt files
    best_practices = (prompts_dir / "best_practices.md").read_text()
    scaffolding_instructions = (prompts_dir / "scaffolding_instructions.md").read_text()

    # Concatenate with proper spacing
    template = best_practices + "\n\n" + scaffolding_instructions

    return template + "\n" + user_input


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


def get_branch_name_and_pr_title_from_prompt(
    dg_context: DgContext,
    user_input: str,
    input_type: type["InputType"],
    diagnostics: ClaudeDiagnostics,
    model: ModelType = "sonnet",
) -> BranchNameGeneration:
    """Invokes Claude under the hood to generate a reasonable, valid
    git branch name and pull request title based on the user's stated goal.
    """
    context_str = input_type.get_context(user_input)

    diagnostics.info(
        category="branch_name_and_title_generation_start",
        message="Starting branch name and PR title generation",
        data={
            "input_type": input_type.__name__,
            "context_length": len(context_str),
        },
    )

    start_time = perf_counter()

    # Generate branch name and PR title separately for reliability
    branch_name = get_branch_name(context_str, input_type, diagnostics, model)
    pr_title = get_pr_title(context_str, input_type, diagnostics, model)

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

    return BranchNameGeneration(
        original_branch_name=branch_name,
        final_branch_name=branch_name,  # Will be updated later if needed
        pr_title=pr_title,
        generation_metadata={
            "duration_ms": duration_ms,
            "input_type": input_type.__name__,
            "context_length": len(context_str),
            "approach": "separate_prompts",
        },
    )


class PrintOutputChannel:
    """Output channel that prints to stdout using click.echo."""

    def write(self, text: str) -> None:
        click.echo(text)


@contextmanager
def enter_waiting_phase(phase_name: str, spin: bool = True) -> Iterator[OutputChannel]:
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


def scaffold_content_for_prompt(
    user_input: str,
    input_type: type[InputType],
    diagnostics: ClaudeDiagnostics,
    verbose: bool,
    use_spinner: bool = True,
    model: ModelType = "sonnet",
) -> None:
    """Scaffolds content for the user's prompt using Claude Code SDK."""
    ensure_claude_sdk_python_version()

    from dagster_dg_cli.cli.scaffold.branch.claude.sdk_client import ClaudeSDKClient

    context_str = input_type.get_context(user_input)
    prompt = load_scaffolding_prompt(context_str)
    allowed_tools = get_allowed_commands_scaffolding() + input_type.additional_allowed_tools()

    with enter_waiting_phase("Scaffolding", spin=use_spinner) as channel:
        with diagnostics.claude_operation(
            operation_name="content_scaffolding",
            error_code="content_scaffolding_failed",
            error_message="Content scaffolding failed with SDK",
        ):
            claude_sdk = ClaudeSDKClient(diagnostics)

            asyncio.run(
                claude_sdk.scaffold_with_streaming(
                    prompt=prompt,
                    allowed_tools=allowed_tools,
                    output_channel=channel,
                    disallowed_tools=["Bash(python:*)", "WebSearch", "WebFetch"],
                    verbose=verbose,
                )
            )

            # AI interaction is already logged by SDK client
            # Success logging is handled by claude_operation

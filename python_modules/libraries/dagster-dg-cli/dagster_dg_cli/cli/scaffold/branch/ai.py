"""AI interaction and input type handling for scaffold branch command."""

import asyncio
import os
from abc import ABC
from contextlib import nullcontext
from pathlib import Path
from time import perf_counter
from typing import Any

import click
from dagster_dg_core.context import DgContext
from dagster_shared.record import record

from dagster_dg_cli.cli.scaffold.branch.claude.sdk_client import ClaudeSDKClient
from dagster_dg_cli.cli.scaffold.branch.diagnostics import ClaudeDiagnosticsService
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
    diagnostics: ClaudeDiagnosticsService,
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
    diagnostics.debug(
        f"{operation_name}_generation",
        f"Generating {operation_name} via Anthropic API",
        {"prompt_length": len(prompt)},
    )

    try:
        # Lazy import to avoid performance regression
        import anthropic

        # Get API key from environment
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is required for direct API calls"
            )

        start_time = perf_counter()

        client = anthropic.Anthropic(api_key=api_key)

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=100,  # Short responses for branch names/titles
            temperature=0.0,  # Deterministic output
            messages=[{"role": "user", "content": prompt}],
        )

        duration_ms = (perf_counter() - start_time) * 1000

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

        diagnostics.info(
            f"{operation_name}_generated",
            f"Successfully generated {operation_name} via Anthropic API",
            {
                operation_name: result,
                "duration_ms": duration_ms,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens
                if response.usage
                else None,
            },
        )

        return result

    except Exception as e:
        diagnostics.error(
            f"{operation_name}_generation_failed",
            f"Failed to generate {operation_name} via Anthropic API",
            {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "prompt_length": len(prompt),
            },
        )
        raise


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
    diagnostics: ClaudeDiagnosticsService,
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
    diagnostics: ClaudeDiagnosticsService,
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
    prompt_path = Path(__file__).parent / "prompts" / "scaffolding.md"
    template = prompt_path.read_text()
    return template + "\n" + user_input


def get_allowed_commands_scaffolding() -> list[str]:
    """Get the list of allowed commands for scaffolding operations."""
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
    diagnostics: ClaudeDiagnosticsService,
) -> BranchNameGeneration:
    """Invokes Claude under the hood to generate a reasonable, valid
    git branch name and pull request title based on the user's stated goal.
    """
    context_str = input_type.get_context(user_input)

    diagnostics.info(
        "branch_name_and_title_generation_start",
        "Starting branch name and PR title generation",
        {
            "input_type": input_type.__name__,
            "context_length": len(context_str),
        },
    )

    start_time = perf_counter()

    # Generate branch name and PR title separately for reliability
    branch_name = get_branch_name(context_str, input_type, diagnostics)
    pr_title = get_pr_title(context_str, input_type, diagnostics)

    duration_ms = (perf_counter() - start_time) * 1000

    diagnostics.info(
        "branch_name_and_title_generated",
        "Successfully generated branch name and PR title",
        {
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


def scaffold_content_for_prompt(
    user_input: str,
    input_type: type[InputType],
    diagnostics: ClaudeDiagnosticsService,
    use_spinner: bool = True,
) -> None:
    """Scaffolds content for the user's prompt using Claude Code SDK."""
    context_str = input_type.get_context(user_input)
    prompt = load_scaffolding_prompt(context_str)
    allowed_tools = get_allowed_commands_scaffolding() + input_type.additional_allowed_tools()

    diagnostics.info(
        "content_scaffolding_start",
        "Starting content scaffolding with Claude Code SDK",
        {
            "input_type": input_type.__name__,
            "context_length": len(context_str),
            "prompt_length": len(prompt),
            "allowed_tools_count": len(allowed_tools),
            "allowed_tools": allowed_tools,
        },
    )

    spinner_ctx = (
        daggy_spinner_context("Scaffolding")
        if use_spinner
        else nullcontext(enter_result=PrintOutputChannel())
    )

    start_time = perf_counter()
    with spinner_ctx as spinner:
        try:
            claude_sdk = ClaudeSDKClient(diagnostics)

            # Run the async SDK operation with verbose mode for debug diagnostics
            verbose_mode = diagnostics.level == "debug"
            messages = asyncio.run(
                claude_sdk.scaffold_with_streaming(
                    prompt=prompt,
                    allowed_tools=allowed_tools,
                    output_channel=spinner,
                    disallowed_tools=["Bash(python:*)", "WebSearch", "WebFetch"],
                    verbose=verbose_mode,
                )
            )

            duration_ms = (perf_counter() - start_time) * 1000

            # AI interaction is already logged by SDK client
            diagnostics.info(
                "content_scaffolding_completed",
                "Content scaffolding completed successfully with SDK",
                {
                    "duration_ms": duration_ms,
                    "messages_count": len(messages),
                },
            )
        except Exception as e:
            duration_ms = (perf_counter() - start_time) * 1000

            diagnostics.error(
                "content_scaffolding_failed",
                "Content scaffolding failed with SDK",
                {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "duration_ms": duration_ms,
                },
            )
            raise

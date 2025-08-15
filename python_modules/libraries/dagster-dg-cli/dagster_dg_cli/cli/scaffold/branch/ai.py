"""AI interaction and input type handling for scaffold branch command."""

import json
from abc import ABC
from contextlib import nullcontext
from pathlib import Path

import click
from dagster_dg_core.context import DgContext

from dagster_dg_cli.utils.claude_utils import run_claude, run_claude_stream
from dagster_dg_cli.utils.ui import daggy_spinner_context

MAX_TURNS = 20


def load_branch_name_prompt(context: str) -> str:
    """Load the branch name prompt template and inject context.

    Args:
        context: The context to inject into the prompt

    Returns:
        The formatted prompt string
    """
    prompt_path = Path(__file__).parent / "prompts" / "branch_name.md"
    template = prompt_path.read_text()
    return template.format(context=context)


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
    dg_context: DgContext, user_input: str, input_type: type[InputType]
) -> tuple[str, str]:
    """Invokes Claude under the hood to generate a reasonable, valid
    git branch name and pull request title based on the user's stated goal.
    """
    output = run_claude(
        dg_context,
        load_branch_name_prompt(input_type.get_context(user_input)),
        input_type.additional_allowed_tools(),
    )
    json_output = json.loads(output.strip())
    return json_output["branch-name"], json_output["pr-title"]


class PrintOutputChannel:
    """Output channel that prints to stdout using click.echo."""

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
            load_scaffolding_prompt(input_type.get_context(user_input)),
            get_allowed_commands_scaffolding() + input_type.additional_allowed_tools(),
            output_channel=spinner,
        )

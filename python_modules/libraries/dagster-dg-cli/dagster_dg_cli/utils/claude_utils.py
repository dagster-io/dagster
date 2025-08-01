import functools
import json
import os
import re
import subprocess
from typing import Any, Optional

import typer
from dagster_dg_core.context import DgContext
from yaspin import Spinner
from yaspin.core import Yaspin

daggy_spinner = Spinner(frames="ଳଢଡଜ", interval=100)


@functools.cache
def find_claude(_dg_context: DgContext) -> Optional[list[str]]:
    """Find the Claude CLI executable.

    Attempts to locate the Claude CLI tool by checking:
    1. If 'claude' is available on the system PATH
    2. If 'claude' is available as a shell alias

    Args:
        _dg_context: DgContext instance (unused but kept for compatibility)

    Returns:
        List containing the command to run Claude, or None if not found
    """
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


def run_claude(
    dg_context: DgContext,
    prompt: str,
    allowed_tools: list[str],
) -> str:
    """Run Claude CLI with the given prompt and allowed tools.

    Executes the Claude CLI tool with a specified prompt and set of allowed tools,
    returning the complete output as a string.

    Args:
        dg_context: DgContext instance for finding Claude executable
        prompt: The prompt to send to Claude
        allowed_tools: List of tool names that Claude is allowed to use

    Returns:
        The complete stdout output from Claude as a string

    Raises:
        AssertionError: If Claude CLI is not found on the system
    """
    claude_cmd = find_claude(dg_context)
    assert claude_cmd is not None
    cmd = [
        *claude_cmd,
        "-p",
        prompt,
        "--allowedTools",
        ",".join(allowed_tools),
    ]
    output = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
    )
    return output.stdout


def render_claude_content(content_json: dict[str, Any]) -> Optional[str]:
    """Render a single Claude content item for display.

    Formats different types of Claude content (tool use, text, tool results) into
    human-readable strings with appropriate styling.

    Args:
        content_json: A single content item from Claude's JSON output

    Returns:
        Formatted string representation of the content, or None if no formatting needed
    """
    content_type = content_json.get("type")
    if content_type == "tool_use":
        if content_json.get("name") == "Bash":
            return typer.style(
                f"  Used tool {content_json.get('input', {}).get('command')} ({content_json.get('input', {}).get('description')})",
                dim=True,
            )
        elif content_json.get("name") == "Edit":
            return typer.style(
                f"  Edit file {content_json.get('input', {}).get('file_path')}",
                dim=True,
            )
        else:
            return typer.style(
                f"  Used tool {content_json.get('name')} {content_json.get('input')}", dim=True
            )
    elif content_type == "text":
        return f"\n{content_json.get('text')}"
    elif content_type == "tool_result":
        # check if tool succeeds, else x
        return None
    else:
        return json.dumps(content_json, indent=2)


def render_claude_output(message_json: dict[str, Any]) -> str:
    """Render a complete Claude message for display.

    Takes a Claude message JSON object and formats all its content items into
    a single display string.

    Args:
        message_json: A complete message object from Claude's JSON output

    Returns:
        Formatted string representation of the entire message
    """
    message_inner = message_json.get("message", {})
    output = ""
    content = message_inner.get("content")
    if isinstance(content, str):
        output += content
    elif isinstance(content, list):
        for content in message_inner.get("content", []):
            content_str = render_claude_content(content)
            if content_str:
                output += f"\n{content_str}"
    return output[1:]


def run_claude_stream(
    dg_context: DgContext,
    prompt: str,
    allowed_tools: list[str],
    verbose: bool = False,
    spinner: Optional[Yaspin] = None,
) -> None:
    """Run Claude CLI with streaming output.

    Executes the Claude CLI tool with streaming JSON output, processing and displaying
    each message as it arrives. Useful for long-running Claude sessions where you want
    to see progress in real-time.

    Args:
        dg_context: DgContext instance for finding Claude executable
        prompt: The prompt to send to Claude
        allowed_tools: List of tool names that Claude is allowed to use
        verbose: If True, display raw JSON output instead of formatted messages
        spinner: Optional spinner context for displaying output

    Raises:
        AssertionError: If Claude CLI is not found on the system
    """
    claude_cmd = find_claude(dg_context)
    assert claude_cmd is not None
    cmd = [
        *claude_cmd,
        "-p",
        prompt,
        "--allowedTools",
        ",".join(allowed_tools),
        "--output-format",
        "stream-json",
        "--disallowedTools",
        "Bash(python:*),WebSearch,WebFetch",
        "--verbose",
    ]
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert process.stdout is not None
    for line in process.stdout:
        try:
            line_json = json.loads(line)
            if verbose and spinner:
                spinner.write(json.dumps(line_json, indent=2))
            else:
                output = render_claude_output(line_json)
                if output and spinner:
                    spinner.write(output)
        except json.JSONDecodeError:
            if spinner:
                spinner.write(line)
            else:
                print(line)  # noqa: T201
    process.wait()

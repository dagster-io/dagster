import functools
import json
import os
import re
import subprocess
from datetime import datetime
from time import perf_counter
from typing import Any, Optional, Protocol

# typer and pydantic imports moved to functions to defer import costs
from dagster_dg_cli.cli.scaffold.branch.diagnostics import AIInteraction, ClaudeDiagnosticsService
from dagster_dg_core.context import DgContext


class OutputChannel(Protocol):
    def write(self, text: str) -> None: ...


@functools.cache
def find_claude() -> list[str]:
    """Find the Claude CLI executable.

    Attempts to locate the Claude CLI tool by checking:
    1. If 'claude' is available on the system PATH
    2. If 'claude' is available as a shell alias

    Returns:
        List containing the command to run Claude
    """
    try:  # on PATH
        subprocess.run(
            ["claude", "--version"],
            check=False,
            capture_output=True,
        )
        return ["claude"]
    except FileNotFoundError:
        # check for alias (auto-updating version recommends registering an alias instead of putting on PATH)
        result = subprocess.run(
            [os.getenv("SHELL", "bash"), "-ic", "type claude"],
            capture_output=True,
            text=True,
            check=False,
        )
        path_match = re.search(r"(/[^\s`\']+)", result.stdout)
        if path_match:
            return [path_match.group(1)]

        raise


def run_claude(
    dg_context: DgContext,
    prompt: str,
    allowed_tools: list[str],
    diagnostics: ClaudeDiagnosticsService,
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
    diagnostics.debug(
        "claude_invocation",
        "Invoking Claude CLI",
        {
            "prompt_length": len(prompt),
            "allowed_tools_count": len(allowed_tools),
            "allowed_tools": allowed_tools,
        },
    )

    claude_cmd = find_claude()
    cmd = [
        *claude_cmd,
        "-p",
        prompt,
        "--allowedTools",
        ",".join(allowed_tools),
    ]

    start_time = perf_counter()
    try:
        output = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
        )
        duration_ms = (perf_counter() - start_time) * 1000

        interaction = AIInteraction(
            correlation_id=diagnostics.correlation_id,
            timestamp=datetime.now().isoformat(),
            prompt=prompt,
            response=output.stdout,
            token_count=None,  # Not available from CLI
            tools_used=allowed_tools,
            duration_ms=duration_ms,
        )
        diagnostics.log_ai_interaction(interaction)

        if output.stderr:
            diagnostics.debug(
                "claude_stderr",
                "Claude CLI stderr output",
                {"stderr": output.stderr},
            )

        return output.stdout
    except Exception as e:
        duration_ms = (perf_counter() - start_time) * 1000

        diagnostics.error(
            "claude_invocation_failed",
            "Claude CLI invocation failed",
            {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "duration_ms": duration_ms,
                "command": cmd,
            },
        )
        raise


def render_claude_content(content_json: dict[str, Any]) -> Optional[str]:
    """Render a single Claude content item for display.

    Formats different types of Claude content (tool use, text, tool results) into
    human-readable strings with appropriate styling.

    Args:
        content_json: A single content item from Claude's JSON output

    Returns:
        Formatted string representation of the content, or None if no formatting needed
    """
    import typer

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
    output_channel: OutputChannel,
    diagnostics: ClaudeDiagnosticsService,
    verbose: bool = False,
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
        output_channel: Channel to write output to

    Raises:
        AssertionError: If Claude CLI is not found on the system
    """
    diagnostics.debug(
        "claude_stream_invocation",
        "Invoking Claude CLI with streaming",
        {
            "prompt_length": len(prompt),
            "allowed_tools_count": len(allowed_tools),
            "allowed_tools": allowed_tools,
            "verbose": verbose,
        },
    )

    claude_cmd = find_claude()
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

    start_time = perf_counter()
    response_content = []

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert process.stdout is not None

        for line in process.stdout:
            line_json = json.loads(line)

            # Collect response content for diagnostics
            response_content.append(line_json)

            if verbose:
                output_channel.write(json.dumps(line_json, indent=2))
            else:
                output = render_claude_output(line_json)
                if output:
                    output_channel.write(output)

        process.wait()
        duration_ms = (perf_counter() - start_time) * 1000

        # Log the streaming interaction
        interaction = AIInteraction(
            correlation_id=diagnostics.correlation_id,
            timestamp=datetime.now().isoformat(),
            prompt=prompt,
            response=f"[STREAMING_RESPONSE_LINES: {len(response_content)}]",
            token_count=None,  # Not available from CLI
            tools_used=allowed_tools,
            duration_ms=duration_ms,
        )
        diagnostics.log_ai_interaction(interaction)

        # Log any stderr output
        if process.stderr:
            stderr_content = process.stderr.read()
            if stderr_content:
                diagnostics.debug(
                    "claude_stream_stderr",
                    "Claude CLI streaming stderr output",
                    {"stderr": stderr_content},
                )

    except Exception as e:
        duration_ms = (perf_counter() - start_time) * 1000

        diagnostics.error(
            "claude_stream_invocation_failed",
            "Claude CLI streaming invocation failed",
            {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "duration_ms": duration_ms,
                "command": cmd,
            },
        )
        raise

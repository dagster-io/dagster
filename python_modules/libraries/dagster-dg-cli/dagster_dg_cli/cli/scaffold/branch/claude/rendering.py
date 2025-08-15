"""Output formatting and display utilities for Claude CLI responses."""

import json
from typing import Any, Optional

from dagster_dg_cli.cli.scaffold.branch.validation import (
    ClaudeAssistantMessage,
    ClaudeErrorResult,
    ClaudeSuccessResult,
    ClaudeSystemInit,
    ClaudeUserMessage,
    SDKMessage,
)


def render_claude_content(content_json: dict[str, Any]) -> Optional[str]:
    """Render a single Claude content item for display.

    Formats different types of Claude content (tool use, text, tool results) into
    human-readable strings with appropriate styling.

    Args:
        content_json: A single content item from Claude's JSON output

    Returns:
        Formatted string representation of the content, or None if no formatting needed
    """
    # Import typer dynamically to defer import costs
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


def render_claude_output(message: SDKMessage) -> str:
    """Render a complete Claude message for display.

    Takes a validated SDKMessage and formats all its content items into
    a single display string.

    Args:
        message: A validated SDKMessage

    Returns:
        Formatted string representation of the entire message
    """
    # Handle validated SDKMessage types
    if isinstance(message, (ClaudeAssistantMessage, ClaudeUserMessage)):
        # Assistant or User messages
        message_inner = message.message
        output = ""
        content = message_inner.get("content")
        if isinstance(content, str):
            output += content
        elif isinstance(content, list):
            for content_item in content:
                content_str = render_claude_content(content_item)
                if content_str:
                    output += f"\n{content_str}"
        return output[1:] if output else ""
    elif isinstance(message, ClaudeSuccessResult):
        # Success result message
        return message.result
    elif isinstance(message, ClaudeErrorResult):
        # Error result message
        error_type = message.subtype.replace("error_", "").replace("_", " ").title()
        return (
            f"Error: {error_type} (after {message.num_turns} turns, ${message.total_cost_usd:.4f})"
        )
    elif isinstance(message, ClaudeSystemInit):
        # System initialization message
        tools_summary = f"{len(message.tools)} tools" if message.tools else "no tools"
        mcp_summary = (
            f"{len(message.mcp_servers)} MCP servers" if message.mcp_servers else "no MCP servers"
        )
        return f"Claude initialized: {message.model} with {tools_summary}, {mcp_summary}"
    else:
        # Fallback for unknown message types
        return f"Unknown message type: {type(message).__name__}"

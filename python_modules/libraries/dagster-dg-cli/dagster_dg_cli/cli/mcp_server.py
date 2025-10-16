import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

import click
from dagster_dg_core.config import normalize_cli_config
from dagster_dg_core.context import DgContext
from dagster_dg_core.shared_options import dg_global_options
from dagster_dg_core.utils import DgClickCommand, DgClickGroup, exit_with_error
from dagster_dg_core.utils.mcp_client.claude_desktop import get_claude_desktop_config_path
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper


@click.group(name="mcp", cls=DgClickGroup, hidden=True)
def mcp_group():
    """Commands to interact with the dg MCP server."""


@mcp_group.command(name="serve", cls=DgClickCommand)
@cli_telemetry_wrapper
def serve_command():
    if sys.version_info[:2] < (3, 10):
        exit_with_error(
            "The MCP server is only supported on Python 3.10 and above. "
            "Please upgrade your Python version and reinstall `dagster-dg-cli`.",
        )

    from dagster_dg_cli.mcp.server import mcp

    mcp.run(transport="stdio")


MCP_CONFIG = {
    "command": "dg",
    "args": ["mcp", "serve"],
}


def _inject_into_mcp_config_json(path: Path) -> None:
    contents = json.loads(path.read_text())
    if not contents.get("mcpServers"):
        contents["mcpServers"] = {}
    contents["mcpServers"]["dagster-dg-cli"] = MCP_CONFIG
    path.write_text(json.dumps(contents, indent=2))


def _find_claude() -> Optional[str]:
    try:
        subprocess.run(["claude", "--version"], check=False)
        return "claude"
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
            return path_match.group(1)
    except FileNotFoundError:
        pass

    return None


@mcp_group.command(name="configure", cls=DgClickCommand)
@dg_global_options
@cli_telemetry_wrapper
@click.argument(
    "mcp_client",
    type=click.Choice(
        [
            "claude-desktop",
            "cursor",
            "claude-code",
            "vscode",
        ]
    ),
)
def configure_mcp_command(
    mcp_client: str,
    **global_options: object,
) -> None:
    """Attempt to add the dg MCP server to the specified MCP client under the key `dagster-dg-cli`."""
    if mcp_client == "claude-desktop":
        _inject_into_mcp_config_json(get_claude_desktop_config_path())
    elif mcp_client == "cursor":
        _inject_into_mcp_config_json(Path.home() / ".cursor" / "mcp.json")
    elif mcp_client == "vscode":
        cli_config = normalize_cli_config(global_options, click.get_current_context())
        dg_context = DgContext.for_project_environment(Path.cwd(), cli_config)
        _inject_into_mcp_config_json(dg_context.root_path / ".vscode" / "mcp.json")
    elif mcp_client == "claude-code":
        claude_cmd = _find_claude()
        if not claude_cmd:
            exit_with_error(
                "Could not find claude code. Please install it from https://github.com/anthropics/claude-code"
            )
        subprocess.run(
            [claude_cmd, "mcp", "remove", "dagster-dg-cli"],
            check=False,
            capture_output=True,
        )
        subprocess.run(
            [claude_cmd, "mcp", "add-json", "dagster-dg-cli", json.dumps(MCP_CONFIG)],
            check=True,
        )

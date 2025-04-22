import sys

import click

from dagster_dg.utils import DgClickCommand, DgClickGroup, exit_with_error
from dagster_dg.utils.telemetry import cli_telemetry_wrapper


@click.group(name="mcp", cls=DgClickGroup, hidden=True)
def mcp_group():
    """Commands to interact with the dagster-dg MCP server."""


@mcp_group.command(name="serve", cls=DgClickCommand)
@cli_telemetry_wrapper
def serve_command():
    if sys.version_info[:2] < (3, 10):
        exit_with_error(
            "The MCP server is only supported on Python 3.10 and above. "
            "Please upgrade your Python version and reinstall `dagster-dg`.",
        )
    from dagster_dg.mcp.server import mcp

    mcp.run(transport="stdio")

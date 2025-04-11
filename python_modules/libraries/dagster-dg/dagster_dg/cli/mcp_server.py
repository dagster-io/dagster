import click

from dagster_dg.utils import DgClickCommand, DgClickGroup
from dagster_dg.utils.telemetry import cli_telemetry_wrapper


@click.group(name="mcp", cls=DgClickGroup, hidden=True)
def mcp_group():
    """Commands to interact with the dagster-dg MCP server."""


@mcp_group.command(name="serve", cls=DgClickCommand)
@cli_telemetry_wrapper
def serve_command():
    from dagster_dg.mcp.server import mcp

    mcp.run(transport="stdio")

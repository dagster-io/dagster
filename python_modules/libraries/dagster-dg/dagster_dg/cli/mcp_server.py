import click

from dagster_dg.utils import DgClickCommand, DgClickGroup


@click.group(name="mcp", cls=DgClickGroup, hidden=True)
def mcp_group():
    """Commands to interact with the dagster-dg MCP server."""


@mcp_group.command(name="serve", cls=DgClickCommand)
def serve_command():
    from dagster_dg.mcp.mcp_server import mcp

    mcp.run(transport="stdio")

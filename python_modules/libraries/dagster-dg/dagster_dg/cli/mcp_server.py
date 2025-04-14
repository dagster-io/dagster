import click
import typer

from dagster_dg.utils import DgClickCommand, DgClickGroup
from dagster_dg.utils.telemetry import cli_telemetry_wrapper


@click.group(name="mcp", cls=DgClickGroup, hidden=True)
def mcp_group():
    """Commands to interact with the dagster-dg MCP server."""


@mcp_group.command(name="serve", cls=DgClickCommand)
@cli_telemetry_wrapper
def serve_command():
    """Start the MCP server."""
    from dagster_dg.mcp.server import mcp

    mcp.run(transport="stdio")


@mcp_group.command(name="tools", cls=DgClickCommand)
@cli_telemetry_wrapper
def tools():
    """List the tools available in the MCP server."""
    import asyncio

    from dagster_dg.mcp.server import mcp

    tools = asyncio.run(mcp.list_tools())
    for tool in tools:
        click.echo(
            typer.style(
                "-" * len(tool.name) + "\n" + tool.name + "\n" + "-" * len(tool.name),
                fg=typer.colors.RED,
                bold=True,
            )
        )
        click.echo(tool.description)
        click.echo("\n")

"""CLI command for agent project context."""

from pathlib import Path

import click
from dagster_dg_core.component import EnvRegistry
from dagster_dg_core.config import normalize_cli_config
from dagster_dg_core.context import DgContext
from dagster_dg_core.shared_options import dg_global_options, dg_path_options
from dagster_dg_core.utils import DgClickCommand
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper

from dagster_dg_cli.cli.agent_project_context.collector import _collect_project_context
from dagster_dg_cli.cli.agent_project_context.formatters import get_formatter


@click.command(name="agent-project-context", cls=DgClickCommand)
@dg_path_options
@dg_global_options
@cli_telemetry_wrapper
@click.option(
    "--output",
    type=click.Choice(["json", "markdown", "xml"]),
    default="markdown",
    help="Output format",
)
def agent_project_context_command(
    target_path: Path,
    output: str,
    **global_options: object,
) -> None:
    """Gather comprehensive project context for AI agent consumption."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.from_file_discovery_and_command_line_config(target_path, cli_config)
    registry = EnvRegistry.from_dg_context(dg_context)

    # Collect structured project context
    context = _collect_project_context(dg_context, registry)

    # Format and output based on choice
    formatter = get_formatter(output)
    result = formatter.format(context)

    click.echo(result)

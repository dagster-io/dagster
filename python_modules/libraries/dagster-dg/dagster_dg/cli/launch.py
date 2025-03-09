import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Optional

import click

from dagster_dg.cli.dev import format_forwarded_option
from dagster_dg.cli.shared_options import dg_global_options
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.utils import DgClickCommand, DgClickGroup


@click.group(name="launch", cls=DgClickGroup)
def launch_group():
    """Commands for launching Dagster runs."""


@launch_group.command(name="assets", cls=DgClickCommand)
@click.option("--select", help="Comma-separated Asset selection to target", required=True)
@click.option("--partition", help="Asset partition to target", required=False)
@click.option(
    "--partition-range",
    help="Asset partition range to target i.e. <start>...<end>",
    required=False,
)
@click.option(
    "--config-json", type=click.STRING, help="JSON string of run config to use for the launched."
)
@dg_global_options
def assets_command(
    select: str,
    partition: Optional[str],
    partition_range: Optional[str],
    config_json: Optional[str],
    **global_options: Mapping[str, object],
):
    """Launch a Dagster asset materialization."""
    forward_options = [
        *format_forwarded_option("--select", select),
        *format_forwarded_option("--partition", partition),
        *format_forwarded_option("--partition-range", partition_range),
        *format_forwarded_option("--config-json", config_json),
    ]

    cli_config = normalize_cli_config(global_options, click.get_current_context())
    dg_context = DgContext.for_workspace_or_project_environment(Path.cwd(), cli_config)

    # TODO - make this work in a workspace and/or cloud context instead of materializing the
    # assets in process. It should use the instance's run launcher to launch a run (or backfill
    # depending on the asset selection) and optionally stream logs from that run or backfill in
    # the command line until it finishes. right now, it only works in a project context in local
    # dev/OSS, and executes the selected assets in process using the "dagster asset materialize"
    # command.
    if not dg_context.is_project:
        raise Exception("Must be run in a dg project context.")

    cmd_location = dg_context.get_executable("dagster")
    click.echo(f"Using {cmd_location}")

    args = [
        "--working-directory",
        str(dg_context.root_path),
        "--module-name",
        str(dg_context.code_location_target_module_name),
    ]

    result = subprocess.run(
        [cmd_location, "asset", "materialize", *args, *forward_options], check=False
    )
    if result.returncode != 0:
        click.echo("Failed to launch assets.")
        click.get_current_context().exit(result.returncode)

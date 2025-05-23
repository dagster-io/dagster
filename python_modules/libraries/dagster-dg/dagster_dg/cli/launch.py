from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Optional

import click

from dagster_dg.cli.shared_options import dg_global_options, dg_path_options
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.utils import DgClickCommand, validate_dagster_availability
from dagster_dg.utils.telemetry import cli_telemetry_wrapper


@click.command(name="launch", cls=DgClickCommand)
@click.option("--assets", help="Comma-separated Asset selection to target", required=True)
@click.option("--partition", help="Asset partition to target", required=False)
@click.option(
    "--partition-range",
    help="Asset partition range to target i.e. <start>...<end>",
    required=False,
)
@click.option(
    "--config-json", type=click.STRING, help="JSON string of config to use for the launched run."
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    help=(
        "Specify one or more run config files. These can also be file patterns."
        " If more than one run config file is captured then those files are merged. Files listed first take precedence."
    ),
    multiple=True,
)
@dg_path_options
@dg_global_options
@cli_telemetry_wrapper
def launch_command(
    assets: str,
    partition: Optional[str],
    partition_range: Optional[str],
    config_json: Optional[str],
    config: Sequence[str],
    path: Path,
    **global_options: Mapping[str, object],
):
    """Launch a Dagster run."""
    cli_config = normalize_cli_config(global_options, click.get_current_context())

    # TODO - make this work in a workspace and/or cloud context instead of materializing the
    # assets in process. It should use the instance's run launcher to launch a run (or backfill
    # depending on the asset selection) and optionally stream logs from that run or backfill in
    # the command line until it finishes. right now, it only works in a project context in local
    # dev/OSS, and executes the selected assets in process using the "dagster asset materialize"
    # command.

    dg_context = DgContext.for_project_environment(path, cli_config)

    validate_dagster_availability()

    from dagster._cli.asset import asset_materialize_command_impl

    asset_materialize_command_impl(
        select=assets,
        partition=partition,
        partition_range=partition_range,
        config=tuple(config),
        config_json=config_json,
        working_directory=str(dg_context.root_path),
        module_name=dg_context.code_location_target_module_name,
    )

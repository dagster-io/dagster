import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Optional

import click
from dagster_shared.cli.json import DagsterCliCommandInvocation, DagsterCliSchema
from dagster_shared.ipc import read_unary_response, write_unary_input
from dagster_shared.utils.temp_files import get_temp_file_name

from dagster_dg.cli.dev import format_forwarded_option
from dagster_dg.cli.shared_options import dg_global_options, dg_path_options
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.utils import DgClickCommand
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
@dg_path_options
@dg_global_options
@cli_telemetry_wrapper
def launch_command(
    assets: str,
    partition: Optional[str],
    partition_range: Optional[str],
    config_json: Optional[str],
    path: Path,
    **global_options: Mapping[str, object],
):
    """Launch a Dagster run."""
    # TODO handle case where the project in question is too old to know about these commands

    # generate schema
    cli_config = normalize_cli_config(global_options, click.get_current_context())

    # TODO - make this work in a workspace and/or cloud context instead of materializing the
    # assets in process. It should use the instance's run launcher to launch a run (or backfill
    # depending on the asset selection) and optionally stream logs from that run or backfill in
    # the command line until it finishes. right now, it only works in a project context in local
    # dev/OSS, and executes the selected assets in process using the "dagster asset materialize"
    # command.

    dg_context = DgContext.for_project_environment(path, cli_config)

    cmd_location = dg_context.get_executable("dagster")
    click.echo(f"Using {cmd_location}")

    with get_temp_file_name() as output_file:
        result = subprocess.run(
            [cmd_location, "json", "schema", "--output-file", output_file], check=True
        )
        json_schema_obj = read_unary_response(output_file, as_type=DagsterCliSchema)

        # validate the available params and capabilities in the schema with what we are about to use, raise an exception
        # if the params we want are not yet available telling you you need to upgrade the underlying project

    forward_options = [
        *format_forwarded_option("--select", assets),
        *format_forwarded_option("--partition", partition),
        *format_forwarded_option("--partition-range", partition_range),
        *format_forwarded_option("--config-json", config_json),
    ]

    is_old_version = False

    if is_old_version:
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
    else:
        with get_temp_file_name() as input_file, get_temp_file_name() as output_file:
            invocation = DagsterCliCommandInvocation(
                name=["dagster", "asset", "materialize"],
                options=dict(
                    select=assets,
                    partition=partition,
                    partition_range=partition_range,
                    config_json=config_json,
                    working_directory=str(dg_context.root_path),
                    module_name=dg_context.code_location_target_module_name,
                ),
            )
            write_unary_input(input_file, invocation)

            result = subprocess.run(
                [
                    cmd_location,
                    "json",
                    "call",
                    "--input-file",
                    input_file,
                    "--output-file",
                    output_file,
                ],
                check=True,
            )

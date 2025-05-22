import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import click
from dagster_shared import check

from dagster_dg.cli.shared_options import dg_global_options, dg_path_options
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.utils import DgClickCommand, validate_dagster_availability
from dagster_dg.utils.telemetry import cli_telemetry_wrapper

if TYPE_CHECKING:
    from dagster import DagsterInstance, DagsterRun

SINGLETON_REPOSITORY_NAME = "__repository__"


@click.command(name="launch", cls=DgClickCommand)
@click.option("--assets", help="Comma-separated Asset selection to target", required=False)
@click.option("--job", help="Job to target", required=False)
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
@click.option(
    "--no-wait", is_flag=True, help="Do not wait for the run to finish and do not stream logs"
)
@dg_path_options
@dg_global_options
@cli_telemetry_wrapper
def launch_command(
    assets: Optional[str],
    job: Optional[str],
    partition: Optional[str],
    partition_range: Optional[str],
    config_json: Optional[str],
    config: Sequence[str],
    path: Path,
    no_wait: bool,
    **global_options: Mapping[str, object],
):
    """Launch a Dagster run."""
    check.invariant(assets is not None or job is not None, "Either assets or job must be provided")
    check.invariant(assets is None or job is None, "Cannot provide both assets and job")

    cli_config = normalize_cli_config(global_options, click.get_current_context())

    # TODO - make this work in a workspace and/or cloud context instead of materializing the
    # assets in process. It should use the instance's run launcher to launch a run (or backfill
    # depending on the asset selection) and optionally stream logs from that run or backfill in
    # the command line until it finishes. right now, it only works in a project context in local
    # dev/OSS, and executes the selected assets in process using the "dagster asset materialize"
    # command.

    dg_context = DgContext.for_project_environment(path, cli_config)

    validate_dagster_availability()
    from dagster._cli.job import job_launch_command_impl
    from dagster._cli.utils import get_possibly_temporary_instance_for_cli

    if assets:
        with get_possibly_temporary_instance_for_cli("``dagster job launch``") as instance:
            run = job_launch_command_impl(
                instance=instance,
                job_name=None,
                config=tuple(config),
                config_json=config_json,
                working_directory=str(dg_context.root_path),
                module_name=[dg_context.code_location_target_module_name],
                repository=SINGLETON_REPOSITORY_NAME,
                location=dg_context.code_location_target_module_name,
                run_id=None,
                tags=None,
                op_selection=None,
                asset_selection=assets,
                should_launch=True,
                partition=partition,
                partition_range=partition_range,
            )
            if not no_wait:
                _poll_run(instance, run)

    elif job:
        with get_possibly_temporary_instance_for_cli("``dagster job launch``") as instance:
            run = job_launch_command_impl(
                instance=instance,
                job_name=job,
                config=tuple(config),
                config_json=config_json,
                working_directory=str(dg_context.root_path),
                module_name=[dg_context.code_location_target_module_name],
                repository=SINGLETON_REPOSITORY_NAME,
                location=dg_context.code_location_target_module_name,
                run_id=None,
                tags=None,
                op_selection=None,
                asset_selection=None,
                should_launch=True,
                partition=partition,
                partition_range=partition_range,
            )
            if not no_wait:
                _poll_run(instance, run)


def _poll_run(instance: "DagsterInstance", run: "DagsterRun"):
    while not check.not_none(instance.get_run_by_id(run.run_id)).is_finished:
        time.sleep(3)

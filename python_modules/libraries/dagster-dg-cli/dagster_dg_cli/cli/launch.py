from collections.abc import Mapping, Sequence
from copy import copy
from pathlib import Path
from typing import Optional

import click
from dagster_dg_core.config import normalize_cli_config
from dagster_dg_core.context import DgContext
from dagster_dg_core.shared_options import dg_global_options, dg_path_options
from dagster_dg_core.utils import DgClickCommand
from dagster_dg_core.utils.telemetry import cli_telemetry_wrapper
from dagster_shared import check
from dagster_shared.cli import PythonPointerOpts, python_pointer_options
from dagster_shared.record import as_dict

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
@dg_path_options
@dg_global_options
@python_pointer_options
@cli_telemetry_wrapper
def launch_command(
    assets: Optional[str],
    job: Optional[str],
    partition: Optional[str],
    partition_range: Optional[str],
    config_json: Optional[str],
    config: Sequence[str],
    target_path: Path,
    **other_options: Mapping[str, object],
):
    """Launch a Dagster run."""
    check.invariant(assets is not None or job is not None, "Either assets or job must be provided")
    check.invariant(assets is None or job is None, "Cannot provide both assets and job")

    # TODO - make this work in a workspace and/or cloud context instead of materializing the
    # assets in process. It should use the instance's run launcher to launch a run (or backfill
    # depending on the asset selection) and optionally stream logs from that run or backfill in
    # the command line until it finishes. right now, it only works in a project context in local
    # dev/OSS, and executes the selected assets in process using the "dagster asset materialize"
    # command.

    pointer_opts = PythonPointerOpts.extract_from_cli_options(copy(other_options))

    if pointer_opts.specifies_target():
        extra_workspace_opts = as_dict(pointer_opts)
    else:
        cli_config = normalize_cli_config(other_options, click.get_current_context())
        dg_context = DgContext.for_project_environment(target_path, cli_config)
        extra_workspace_opts = dg_context.target_args

    if assets:
        from dagster._cli.asset import asset_materialize_command_impl

        asset_materialize_command_impl(
            select=assets,
            partition=partition,
            partition_range=partition_range,
            config=tuple(config),
            config_json=config_json,
            **extra_workspace_opts,
        )

    elif job:
        from dagster._cli.job import job_execute_command_impl

        job_execute_command_impl(
            job_name=job,
            config=tuple(config),
            config_json=config_json,
            tags=None,
            op_selection=None,
            partition=partition,
            partition_range=partition_range,
            repository=None,
            **extra_workspace_opts,
        )

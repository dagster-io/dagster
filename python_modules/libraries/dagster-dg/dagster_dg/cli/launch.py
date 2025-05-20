import json
import subprocess
from collections.abc import Mapping
from pathlib import Path

import click
from dagster_shared.utils.cli import schema_to_parameters

from dagster_dg.cli.shared_options import dg_global_options, dg_path_options
from dagster_dg.config import (
    get_config_from_cli_context,
    normalize_cli_config,
    set_config_on_cli_context,
)
from dagster_dg.context import DgContext
from dagster_dg.utils import DgClickCommand
from dagster_dg.utils.telemetry import cli_telemetry_wrapper


class DgDynamicCommand(DgClickCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._params_defined = False

    def _define_params(self, cli_context: click.Context) -> None:
        cli_config = normalize_cli_config({}, cli_context)
        set_config_on_cli_context(cli_context, cli_config)

        # Uhhh what to do about this?
        config = get_config_from_cli_context(cli_context)
        # This will raise an error if you try to run dg launch outside of a project context

        # Not clear that Path.cwd() is right here - can we somehow get the path option if it is set??
        dg_context = DgContext.for_project_environment(Path.cwd(), config)
        cmd_location = dg_context.get_executable("dagster")
        result_schema = json.loads(
            subprocess.run([cmd_location, "json"], check=False, capture_output=True).stdout.decode()
        )

        print(str(result_schema))
        asset_materialize_schema = next(
            iter(
                [schema for command, schema in result_schema if command == ["asset", "materialize"]]
            )
        )
        self.params.extend(schema_to_parameters(asset_materialize_schema))
        self._params_defined = True

    def get_help_option_names(self, ctx: click.Context):
        if not self._params_defined:
            self._define_params(ctx)
        return super().get_help_option_names(ctx)

    def get_params(self, ctx: click.Context):
        if not self._params_defined:
            self._define_params(ctx)
        return super().get_params(ctx)


@click.command(name="launch", cls=DgDynamicCommand)
@dg_path_options
@dg_global_options
@cli_telemetry_wrapper
def launch_command(
    path: Path,
    **options: Mapping[str, object],
):
    print(str(options))

    ## How do we distinguish between forwarded options and global options here

    """Launch a Dagster run."""

    # need to filter this down to global options
    cli_config = normalize_cli_config({}, click.get_current_context())

    # TODO - make this work in a workspace and/or cloud context instead of materializing the
    # assets in process. It should use the instance's run launcher to launch a run (or backfill
    # depending on the asset selection) and optionally stream logs from that run or backfill in
    # the command line until it finishes. right now, it only works in a project context in local
    # dev/OSS, and executes the selected assets in process using the "dagster asset materialize"
    # command.

    dg_context = DgContext.for_project_environment(path, cli_config)

    cmd_location = dg_context.get_executable("dagster")
    click.echo(f"Using {cmd_location}")

    input_args = {**options}
    input_args["working-directory"] = str(dg_context.root_path)
    input_args["module-name"] = str(dg_context.code_location_target_module_name)

    forwarded_options = []
    for key, val in input_args.items():
        # this is a gross way of excluding the global options, need a better way

        if key in {"path", "cache_dir", "disable_cache", "verbose", "use_component_modules"}:
            continue

        if val:
            forwarded_options.extend([f"--{key}", val])

    result = subprocess.run([cmd_location, "asset", "materialize", *forwarded_options], check=False)
    if result.returncode != 0:
        click.echo("Failed to launch assets.")
        click.get_current_context().exit(result.returncode)

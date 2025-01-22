from pathlib import Path
from typing import Annotated

import click
import typer
from typer_di import Depends, TyperDI

from dagster_dg.cli.code_location import code_location_group
from dagster_dg.cli.component import component_group
from dagster_dg.cli.component_type import component_type_group
from dagster_dg.cli.deployment import deployment_group
from dagster_dg.cli.global_options import typer_dg_global_options
from dagster_dg.component import RemoteComponentRegistry
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.utils import exit_with_error
from dagster_dg.version import __version__

DG_CLI_MAX_OUTPUT_WIDTH = 120


def create_dg_cli():
    app = TyperDI(name="dg")
    # app = typer.Typer(name="dg")

    app.add_typer(code_location_group, name="code-location")
    app.add_typer(deployment_group, name="deployment")
    # app.add_typer(component_group, name="component")
    app.add_typer(component_type_group, name="component-type")

    # context_settings={
    #     "max_content_width": DG_CLI_MAX_OUTPUT_WIDTH,
    #     "help_option_names": ["-h", "--help"],
    # },
    # invoke_without_command=True,

    @app.callback()
    def callback(
        context: typer.Context,
        clear_cache: Annotated[bool, typer.Option(help="Clear the cache.")] = False,
        rebuild_component_registry: Annotated[
            bool,
            typer.Option(
                help="Recompute and cache the set of available component types for the current environment. Note that this also happens automatically whenever the cache is detected to be stale.",
            ),
        ] = False,
        version: Annotated[bool, typer.Option(help="Show the version and exit.")] = False,
        global_options: dict[str, object] = Depends(typer_dg_global_options),
    ):
        """CLI for working with Dagster components."""
        if version:
            click.echo(f"dg version: {__version__}")
            context.exit(0)
        if clear_cache and rebuild_component_registry:
            exit_with_error("Cannot specify both --clear-cache and --rebuild-component-registry.")
        elif clear_cache:
            cli_config = normalize_cli_config(global_options, context)
            dg_context = DgContext.from_config_file_discovery_and_cli_config(Path.cwd(), cli_config)
            dg_context.cache.clear_all()
            if context.invoked_subcommand is None:
                context.exit(0)
        elif rebuild_component_registry:
            cli_config = normalize_cli_config(global_options, context)
            dg_context = DgContext.from_config_file_discovery_and_cli_config(Path.cwd(), cli_config)
            if context.invoked_subcommand is not None:
                exit_with_error("Cannot specify --rebuild-component-registry with a subcommand.")
            _rebuild_component_registry(dg_context)
        elif context.invoked_subcommand is None:
            click.echo(context.get_help())
            context.exit(0)

    typer_click_object = typer.main.get_group(app)
    typer_click_object.context_settings = {
        "max_content_width": DG_CLI_MAX_OUTPUT_WIDTH,
        "help_option_names": ["-h", "--help"],
    }
    typer_click_object.invoke_without_command = True
    typer_click_object.add_command(component_group)

    return typer_click_object


def _rebuild_component_registry(dg_context: DgContext):
    if not dg_context.is_code_location:
        exit_with_error("This command must be run inside a Dagster code location directory.")
    elif not dg_context.has_cache:
        exit_with_error("Cache is disabled. This command cannot be run without a cache.")
    elif not dg_context.config.use_dg_managed_environment:
        exit_with_error(
            "Cannot rebuild the component registry with environment management disabled."
        )
    dg_context.ensure_uv_lock()
    key = dg_context.get_cache_key("component_registry_data")
    dg_context.cache.clear_key(key)
    # This will trigger a rebuild of the component registry
    RemoteComponentRegistry.from_dg_context(dg_context)


ENV_PREFIX = "DAGSTER_DG"
cli = create_dg_cli()


def main():
    cli(auto_envvar_prefix=ENV_PREFIX)

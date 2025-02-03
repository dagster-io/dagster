from pathlib import Path

import click

from dagster_dg.cli.code_location import code_location_group
from dagster_dg.cli.component import component_group
from dagster_dg.cli.component_type import component_type_group
from dagster_dg.cli.deployment import deployment_group
from dagster_dg.cli.global_options import dg_global_options
from dagster_dg.component import RemoteComponentRegistry
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.utils import DgClickGroup, exit_with_error
from dagster_dg.version import __version__

DG_CLI_MAX_OUTPUT_WIDTH = 120


def create_dg_cli():
    @click.group(
        name="dg",
        commands={
            "code-location": code_location_group,
            "deployment": deployment_group,
            "component": component_group,
            "component-type": component_type_group,
        },
        context_settings={
            "max_content_width": DG_CLI_MAX_OUTPUT_WIDTH,
            "help_option_names": ["-h", "--help"],
        },
        invoke_without_command=True,
        cls=DgClickGroup,
    )
    @dg_global_options
    @click.option(
        "--clear-cache",
        is_flag=True,
        help="Clear the cache.",
        default=False,
    )
    @click.option(
        "--rebuild-component-registry",
        is_flag=True,
        help=(
            "Recompute and cache the set of available component types for the current environment."
            " Note that this also happens automatically whenever the cache is detected to be stale."
        ),
        default=False,
    )
    @click.option(
        "--install-completion",
        is_flag=True,
        help="Automatically detect your shell and install a completion script for the `dg` command. This will append to your shell startup file.",
        default=False,
    )
    @click.version_option(__version__, "--version", "-v")
    @click.pass_context
    def group(
        context: click.Context,
        install_completion: bool,
        clear_cache: bool,
        rebuild_component_registry: bool,
        **global_options: object,
    ):
        """CLI for working with Dagster components."""
        if install_completion:
            import dagster_dg.completion

            dagster_dg.completion.install_completion(context)
            context.exit(0)
        elif clear_cache and rebuild_component_registry:
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

    return group


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

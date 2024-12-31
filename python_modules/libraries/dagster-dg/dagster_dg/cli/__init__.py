import sys
from pathlib import Path

import click

from dagster_dg.cli.code_location import code_location_group
from dagster_dg.cli.component import component_group
from dagster_dg.cli.component_type import component_type_group
from dagster_dg.cli.deployment import deployment_group
from dagster_dg.cli.global_options import dg_global_options
from dagster_dg.context import (
    DgContext,
    ensure_uv_lock,
    fetch_component_registry,
    is_inside_code_location_directory,
    make_cache_key,
    resolve_code_location_root_directory,
)
from dagster_dg.utils import DgClickGroup
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
    @click.version_option(__version__, "--version", "-v")
    @click.pass_context
    def group(
        context: click.Context,
        clear_cache: bool,
        rebuild_component_registry: bool,
        **global_options: object,
    ):
        """CLI for working with Dagster components."""
        if clear_cache and rebuild_component_registry:
            click.echo(
                click.style(
                    "Cannot specify both --clear-cache and --rebuild-component-registry.", fg="red"
                )
            )
            sys.exit(1)
        elif clear_cache:
            dg_context = DgContext.from_cli_global_options(global_options)
            dg_context.cache.clear_all()
            if context.invoked_subcommand is None:
                context.exit(0)
        elif rebuild_component_registry:
            dg_context = DgContext.from_cli_global_options(global_options)
            if context.invoked_subcommand is not None:
                click.echo(
                    click.style(
                        "Cannot specify --rebuild-component-registry with a subcommand.", fg="red"
                    )
                )
                sys.exit(1)
            _rebuild_component_registry(dg_context)
        elif context.invoked_subcommand is None:
            click.echo(context.get_help())
            context.exit(0)

    return group


def _rebuild_component_registry(dg_context: DgContext):
    if not is_inside_code_location_directory(Path.cwd()):
        click.echo(
            click.style(
                "This command must be run inside a Dagster code location directory.", fg="red"
            )
        )
        sys.exit(1)
    if not dg_context.has_cache:
        click.echo(
            click.style("Cache is disabled. This command cannot be run without a cache.", fg="red")
        )
        sys.exit(1)
    root_path = resolve_code_location_root_directory(Path.cwd())
    ensure_uv_lock(root_path)
    key = make_cache_key(root_path, "component_registry_data")
    dg_context.cache.clear_key(key)
    # This will trigger a rebuild of the component registry
    fetch_component_registry(Path.cwd(), dg_context)


ENV_PREFIX = "DAGSTER_DG"
cli = create_dg_cli()


def main():
    cli(auto_envvar_prefix=ENV_PREFIX)

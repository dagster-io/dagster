import sys
from pathlib import Path

import click

from dagster_dg.cache import DgCache
from dagster_dg.cli.code_location import code_location_group
from dagster_dg.cli.component import component_group
from dagster_dg.cli.component_type import component_type_group
from dagster_dg.cli.deployment import deployment_group
from dagster_dg.config import DgConfig, set_config_on_cli_context
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


def create_dg_cli():
    commands = {
        "code-location": code_location_group,
        "deployment": deployment_group,
        "component": component_group,
        "component-type": component_type_group,
    }

    # Defaults are defined on the DgConfig object.
    @click.group(
        commands=commands,
        context_settings={"max_content_width": 120, "help_option_names": ["-h", "--help"]},
        invoke_without_command=True,
        cls=DgClickGroup,
    )
    @click.option(
        "--builtin-component-lib",
        type=str,
        default=DgConfig.builtin_component_lib,
        help="Specify a builitin component library to use.",
    )
    @click.option(
        "--verbose",
        is_flag=True,
        default=DgConfig.verbose,
        help="Enable verbose output for debugging.",
    )
    @click.option(
        "--disable-cache",
        is_flag=True,
        default=DgConfig.disable_cache,
        help="Disable caching of component registry data.",
    )
    @click.option(
        "--clear-cache",
        is_flag=True,
        help="Clear the cache before running the command.",
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
        "--cache-dir",
        type=Path,
        default=DgConfig.cache_dir,
        help="Specify a directory to use for the cache.",
    )
    @click.version_option(__version__, "--version", "-v")
    @click.pass_context
    def group(
        context: click.Context,
        builtin_component_lib: str,
        verbose: bool,
        disable_cache: bool,
        cache_dir: Path,
        clear_cache: bool,
        rebuild_component_registry: bool,
    ):
        """CLI tools for working with Dagster components."""
        context.ensure_object(dict)
        config = DgConfig(
            builtin_component_lib=builtin_component_lib,
            verbose=verbose,
            disable_cache=disable_cache,
            cache_dir=cache_dir,
        )
        set_config_on_cli_context(context, config)

        if clear_cache and rebuild_component_registry:
            click.echo(
                click.style(
                    "Cannot specify both --clear-cache and --rebuild-component-registry.", fg="red"
                )
            )
            sys.exit(1)
        elif clear_cache:
            DgCache.from_config(config).clear_all()
            if context.invoked_subcommand is None:
                context.exit(0)
        elif rebuild_component_registry:
            if context.invoked_subcommand is not None:
                click.echo(
                    click.style(
                        "Cannot specify --rebuild-component-registry with a subcommand.", fg="red"
                    )
                )
                sys.exit(1)
            _rebuild_component_registry(context)
        elif context.invoked_subcommand is None:
            click.echo(context.get_help())
            context.exit(0)

    return group


def _rebuild_component_registry(cli_context: click.Context):
    dg_context = DgContext.from_cli_context(cli_context)
    if not is_inside_code_location_directory(Path.cwd()):
        click.echo(
            click.style(
                "This command must be run inside a Dagster code location directory.", fg="red"
            )
        )
        sys.exit(1)
    if not dg_context.cache:
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

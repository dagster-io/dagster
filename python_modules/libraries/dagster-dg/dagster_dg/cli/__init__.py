import os
from pathlib import Path

import click

from dagster_dg.cache import DgCache
from dagster_dg.cli.check import check_group
from dagster_dg.cli.dev import dev_command
from dagster_dg.cli.docs import docs_group
from dagster_dg.cli.init import init_command
from dagster_dg.cli.launch import launch_command
from dagster_dg.cli.list import list_group
from dagster_dg.cli.mcp_server import mcp_group
from dagster_dg.cli.plus import plus_group
from dagster_dg.cli.scaffold import scaffold_group
from dagster_dg.cli.shared_options import dg_global_options, dg_path_options
from dagster_dg.cli.utils import utils_group
from dagster_dg.component import RemotePluginRegistry
from dagster_dg.config import normalize_cli_config
from dagster_dg.context import DgContext
from dagster_dg.utils import DgClickGroup, exit_with_error
from dagster_dg.version import __version__

DG_CLI_MAX_OUTPUT_WIDTH = 120


def create_dg_cli():
    @click.group(
        name="dg",
        commands={
            "check": check_group,
            "docs": docs_group,
            "utils": utils_group,
            "launch": launch_command,
            "list": list_group,
            "scaffold": scaffold_group,
            "dev": dev_command,
            "init": init_command,
            "plus": plus_group,
            "mcp": mcp_group,
        },
        context_settings={
            "max_content_width": DG_CLI_MAX_OUTPUT_WIDTH,
            "help_option_names": ["-h", "--help"],
        },
        invoke_without_command=True,
        cls=DgClickGroup,
    )
    @dg_path_options
    @dg_global_options
    @click.option(
        "--clear-cache",
        is_flag=True,
        help="Clear the cache.",
        default=False,
    )
    @click.option(
        "--rebuild-plugin-cache",
        is_flag=True,
        help=(
            "Refetch and cache the set of available dg plugins and associated plugin objects for the current environment."
            " Note that this also happens automatically whenever the plugin cache is detected to be stale."
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
    def group(
        install_completion: bool,
        clear_cache: bool,
        rebuild_plugin_cache: bool,
        path: Path,
        **global_options: object,
    ):
        """CLI for managing Dagster projects."""
        os.environ["DAGSTER_IS_DEV_CLI"] = "1"

        context = click.get_current_context()
        if install_completion:
            import dagster_dg.completion

            dagster_dg.completion.install_completion(context)
            context.exit(0)
        elif clear_cache and rebuild_plugin_cache:
            exit_with_error("Cannot specify both --clear-cache and --rebuild-plugin-cache.")
        elif clear_cache:
            cli_config = normalize_cli_config(global_options, context)
            dg_context = DgContext.from_file_discovery_and_command_line_config(path, cli_config)
            # Normally we would access the cache through the DgContext, but cache is currently
            # disabled outside of a project context. When that restriction is lifted, we will change
            # this to access the cache through the DgContext.
            cache = DgCache.from_config(dg_context.config)
            cache.clear_all()
            if context.invoked_subcommand is None:
                context.exit(0)
        elif rebuild_plugin_cache:
            cli_config = normalize_cli_config(global_options, context)
            dg_context = DgContext.for_defined_registry_environment(path, cli_config)
            if context.invoked_subcommand is not None:
                exit_with_error("Cannot specify --rebuild-plugin-cache with a subcommand.")
            _rebuild_plugin_cache(dg_context)
        elif context.invoked_subcommand is None:
            click.echo(context.get_help())
            context.exit(0)

    return group


def _rebuild_plugin_cache(dg_context: DgContext):
    if not dg_context.is_plugin_cache_enabled:
        exit_with_error("Plugin cache is disabled. This command cannot be run without a cache.")
    dg_context.ensure_uv_lock()
    key = dg_context.get_cache_key("plugin_registry_data")
    dg_context.cache.clear_key(key)
    # This will trigger a rebuild of the plugin cache
    RemotePluginRegistry.from_dg_context(dg_context)


ENV_PREFIX = "DAGSTER_DG"
cli = create_dg_cli()


def main():
    cli(auto_envvar_prefix=ENV_PREFIX)

from pathlib import Path

import click

from dagster_dg.cache import DgCache
from dagster_dg.cli.generate import generate_cli
from dagster_dg.cli.info import info_cli
from dagster_dg.cli.list import list_cli
from dagster_dg.config import DgConfig, set_config_on_cli_context
from dagster_dg.version import __version__


def create_dg_cli():
    commands = {
        "generate": generate_cli,
        "info": info_cli,
        "list": list_cli,
    }

    # Defaults are defined on the DgConfig object.
    @click.group(
        commands=commands,
        context_settings={"max_content_width": 120, "help_option_names": ["-h", "--help"]},
        invoke_without_command=True,
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
    ):
        """CLI tools for working with Dagster components."""
        context.ensure_object(dict)
        config = DgConfig(
            builtin_component_lib=builtin_component_lib,
            verbose=verbose,
            disable_cache=disable_cache,
            cache_dir=cache_dir,
        )
        if clear_cache:
            DgCache.from_config(config).clear()
            if context.invoked_subcommand is None:
                context.exit(0)
        elif context.invoked_subcommand is None:
            click.echo(context.get_help())
            context.exit(0)

        set_config_on_cli_context(context, config)

    return group


ENV_PREFIX = "DAGSTER_DG"
cli = create_dg_cli()


def main():
    cli(auto_envvar_prefix=ENV_PREFIX)

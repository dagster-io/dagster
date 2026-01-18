import os
from pathlib import Path

import click
from dagster_dg_core.shared_options import dg_global_options, dg_path_options
from dagster_dg_core.utils import DG_CLI_MAX_OUTPUT_WIDTH, DgClickGroup

from dagster_dg_cli.cli.api import api_group
from dagster_dg_cli.cli.check import check_group
from dagster_dg_cli.cli.dev import dev_command
from dagster_dg_cli.cli.launch import launch_command
from dagster_dg_cli.cli.list import list_group
from dagster_dg_cli.cli.mcp_server import mcp_group
from dagster_dg_cli.cli.plus import plus_group
from dagster_dg_cli.cli.scaffold import scaffold_group
from dagster_dg_cli.cli.utils import utils_group
from dagster_dg_cli.version import __version__


def create_dg_cli():
    @click.group(
        name="dg",
        commands={
            "api": api_group,
            "check": check_group,
            "utils": utils_group,
            "launch": launch_command,
            "list": list_group,
            "scaffold": scaffold_group,
            "dev": dev_command,
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
        "--install-completion",
        is_flag=True,
        help="Automatically detect your shell and install a completion script for the `dg` command. This will append to your shell startup file.",
        default=False,
    )
    @click.version_option(__version__, "--version", "-v")
    def group(
        install_completion: bool,
        target_path: Path,
        **global_options: object,
    ):
        """CLI for managing Dagster projects."""
        os.environ["DAGSTER_IS_DEV_CLI"] = "1"

        context = click.get_current_context()
        if install_completion:
            import dagster_dg_core.completion

            dagster_dg_core.completion.install_completion(context)
            context.exit(0)
        elif context.invoked_subcommand is None:
            click.echo(context.get_help())
            context.exit(0)

    return group


ENV_PREFIX = "DAGSTER_DG"
cli = create_dg_cli()


def main():
    cli(auto_envvar_prefix=ENV_PREFIX)

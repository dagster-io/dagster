"""Textual-based CLI for dagster-dg."""

import os
from pathlib import Path

import click
from dagster_dg_core.shared_options import dg_global_options, dg_path_options
from dagster_dg_core.utils import DG_CLI_MAX_OUTPUT_WIDTH, DgClickGroup

from dagster_dg_cli.cli_textual.scaffold import scaffold_group
from dagster_dg_cli.version import __version__


def create_dg_web_cli():
    @click.group(
        name="dg-web",
        commands={
            "scaffold": scaffold_group,
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
    @click.version_option(__version__, "--version", "-v")
    def group(
        target_path: Path,
        **global_options: object,
    ):
        """Textual-based CLI for managing Dagster projects."""
        os.environ["DAGSTER_IS_DEV_CLI"] = "1"

        context = click.get_current_context()
        if context.invoked_subcommand is None:
            click.echo(context.get_help())
            context.exit(0)

    return group


ENV_PREFIX = "DAGSTER_DG_WEB"
cli = create_dg_web_cli()


def main():
    cli(auto_envvar_prefix=ENV_PREFIX)

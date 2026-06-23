import builtins
import os
from pathlib import Path

import click
from dagster_dg_core.shared_options import dg_global_options, dg_path_options
from dagster_dg_core.utils import DG_CLI_MAX_OUTPUT_WIDTH, DgClickGroup

from dagster_dg_cli.version import __version__


class DgCliGroup(DgClickGroup):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._commands_defined = False

    def get_command(self, ctx: click.Context, cmd_name: str) -> "click.Command | None":
        if cmd_name not in self.commands:
            self._define_commands()
        return super().get_command(ctx, cmd_name)

    def list_commands(self, ctx: click.Context) -> builtins.list[str]:
        self._define_commands()
        return super().list_commands(ctx)

    def _define_commands(self) -> None:
        if self._commands_defined:
            return

        # Lazy command registration keeps the top-level dg CLI import lightweight.
        from dagster_dg_cli.cli.api import api_group
        from dagster_dg_cli.cli.check import check_group
        from dagster_dg_cli.cli.dev import dev_command
        from dagster_dg_cli.cli.labs import labs_group
        from dagster_dg_cli.cli.launch import launch_command
        from dagster_dg_cli.cli.list import list_group
        from dagster_dg_cli.cli.plus import plus_group
        from dagster_dg_cli.cli.scaffold import scaffold_group
        from dagster_dg_cli.cli.utils import utils_group

        self.add_command(check_group)
        self.add_command(utils_group)
        self.add_command(launch_command)
        self.add_command(list_group)
        self.add_command(scaffold_group)
        self.add_command(dev_command)
        self.add_command(api_group)
        self.add_command(labs_group)
        self.add_command(plus_group)
        self._commands_defined = True


def create_dg_cli():
    @click.group(
        name="dg",
        context_settings={
            "max_content_width": DG_CLI_MAX_OUTPUT_WIDTH,
            "help_option_names": ["-h", "--help"],
        },
        invoke_without_command=True,
        cls=DgCliGroup,
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

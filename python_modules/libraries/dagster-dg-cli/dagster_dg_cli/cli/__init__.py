import os
from pathlib import Path
from typing import Optional

import click
from dagster_dg_core.shared_options import dg_global_options, dg_path_options
from dagster_dg_core.utils import DG_CLI_MAX_OUTPUT_WIDTH, DgClickGroup

from dagster_dg_cli.version import __version__

# Lazy loading map for commands
_LAZY_COMMANDS = {
    "api": "dagster_dg_cli.cli.api:api_group",
    "check": "dagster_dg_cli.cli.check:check_group",
    "dev": "dagster_dg_cli.cli.dev:dev_command",
    "docs": "dagster_dg_cli.cli.docs:docs_group",
    "launch": "dagster_dg_cli.cli.launch:launch_command",
    "list": "dagster_dg_cli.cli.list:list_group",
    "mcp": "dagster_dg_cli.cli.mcp_server:mcp_group",
    "plus": "dagster_dg_cli.cli.plus:plus_group",
    "scaffold": "dagster_dg_cli.cli.scaffold:scaffold_group",
    "utils": "dagster_dg_cli.cli.utils:utils_group",
}


class LazyDgClickGroup(DgClickGroup):
    """A Click group that loads commands lazily to avoid expensive imports at startup."""

    def get_command(self, ctx: click.Context, cmd_name: str) -> Optional[click.Command]:
        # First check if command is already loaded
        if cmd_name in self.commands:
            return self.commands[cmd_name]

        # Try to load lazily
        if cmd_name in _LAZY_COMMANDS:
            module_path, attr_name = _LAZY_COMMANDS[cmd_name].split(":")
            try:
                import importlib

                module = importlib.import_module(module_path)
                command = getattr(module, attr_name)
                self.add_command(command, cmd_name)
                return command
            except (ImportError, AttributeError):
                pass

        return None

    def list_commands(self, ctx: click.Context) -> list[str]:
        return sorted(list(_LAZY_COMMANDS.keys()))


def create_dg_cli():
    @click.group(
        name="dg",
        context_settings={
            "max_content_width": DG_CLI_MAX_OUTPUT_WIDTH,
            "help_option_names": ["-h", "--help"],
        },
        invoke_without_command=True,
        cls=LazyDgClickGroup,
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

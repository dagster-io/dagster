from textwrap import dedent

import click
from dagster_dg_core.utils import DgClickGroup
from rich.console import Console
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from typer import rich_utils

from dagster_dg_cli.cli.ai.dispatch import dispatch_command
from dagster_dg_cli.cli.scaffold.github_actions_ai_dispatch import (
    labs_scaffold_github_actions_ai_dispatch_command,
)

_LABS_ASCII_ART_COMPACT = dedent(r"""
          .:::::::.          
      .-+***********+-.      
    -+*********=-=+****+:    
  :+**********. :=::*****+.  
 :************.+#@@.+******. 
.******************+******** 
-****##*********************-
-**##**********##+***#******=
.****##*******##+ =*+.+*++**-
 .=*********##*-.=*+.:**.:**.
   .-=**##**=:.-**=.-**.:**: 
  .**=--::--=+*+-.:+*=.-**:  
   .:-======-:::=**=:-+*=.   
          =++**+=:   --.     
          :::.               
""").strip("\n")


def _get_console() -> Console:
    return Console(
        theme=Theme(
            {
                "option": rich_utils.STYLE_OPTION,
                "switch": rich_utils.STYLE_SWITCH,
                "negative_option": rich_utils.STYLE_NEGATIVE_OPTION,
                "negative_switch": rich_utils.STYLE_NEGATIVE_SWITCH,
                "metavar": rich_utils.STYLE_METAVAR,
                "metavar_sep": rich_utils.STYLE_METAVAR_SEPARATOR,
                "usage": rich_utils.STYLE_USAGE,
            }
        ),
        highlighter=rich_utils.highlighter,
        color_system=rich_utils.COLOR_SYSTEM,
        force_terminal=rich_utils.FORCE_TERMINAL,
        width=rich_utils.MAX_WIDTH,
    )


def _print_labs_header(console: Console, help_text: str) -> None:
    art = Text(_LABS_ASCII_ART_COMPACT, style="magenta")
    description = Text(
        f"{help_text}\n\n"
        "The commands found in this namespace are subject to change. Use them at your own risk!\n\n"
        "If you would like to learn more about the other experiments being built at Dagster Labs "
        "be sure to check out the documentation at https://docs.dagster.io/guides/labs"
    )

    header_table = Table.grid(expand=True, padding=(0, 2))
    header_table.add_column(width=max(len(line) for line in _LABS_ASCII_ART_COMPACT.splitlines()))
    header_table.add_column(ratio=1)
    header_table.add_row(art, description)

    console.print(
        Panel(
            header_table,
            border_style=rich_utils.STYLE_OPTIONS_PANEL_BORDER,
            title="Labs",
            title_align=rich_utils.ALIGN_OPTIONS_PANEL,
        )
    )


class LabsClickGroup(DgClickGroup):
    def format_help(self, context: click.Context, formatter: click.HelpFormatter) -> None:
        console = _get_console()

        console.print(
            Padding(rich_utils.highlighter(self.get_usage(context)), 1),
            style=rich_utils.STYLE_USAGE_COMMAND,
        )

        _print_labs_header(console, self.help or "")

        options_table = Table(
            highlight=True, show_header=False, expand=True, box=None, padding=(0, 1)
        )
        options_table.add_column(style=rich_utils.STYLE_OPTION, no_wrap=True)
        options_table.add_column(style=rich_utils.STYLE_SWITCH, no_wrap=True)
        options_table.add_column(ratio=1)

        for param in self.get_params(context):
            if getattr(param, "hidden", False) or not isinstance(param, click.Option):
                continue
            long_opts = ",".join(opt for opt in param.opts if opt.startswith("--"))
            short_opts = ",".join(opt for opt in param.opts if not opt.startswith("--"))
            help_text = param.help or ""
            options_table.add_row(long_opts, short_opts, help_text)

        if options_table.row_count:
            console.print(
                Panel(
                    options_table,
                    border_style=rich_utils.STYLE_OPTIONS_PANEL_BORDER,
                    title=rich_utils.OPTIONS_PANEL_TITLE,
                    title_align=rich_utils.ALIGN_OPTIONS_PANEL,
                )
            )

        commands = [
            command
            for command_name in self.list_commands(context)
            if (command := self.get_command(context, command_name)) and not command.hidden
        ]
        max_cmd_len = max((len(command.name or "") for command in commands), default=0)

        commands_table = Table(
            highlight=False, show_header=False, expand=True, box=None, padding=(0, 1)
        )
        commands_table.add_column(
            style=rich_utils.STYLE_COMMANDS_TABLE_FIRST_COLUMN, no_wrap=True, width=max_cmd_len
        )
        commands_table.add_column(ratio=1)

        for command in commands:
            commands_table.add_row(command.name or "", command.short_help or command.help or "")

        if commands_table.row_count:
            console.print(
                Panel(
                    commands_table,
                    border_style=rich_utils.STYLE_COMMANDS_PANEL_BORDER,
                    title=rich_utils.COMMANDS_PANEL_TITLE,
                    title_align=rich_utils.ALIGN_COMMANDS_PANEL,
                )
            )


@click.group(name="labs", cls=LabsClickGroup, invoke_without_command=True)
@click.pass_context
def labs_group(context: click.Context) -> None:
    """Experimental commands of the `dg` command-line utility."""
    if context.invoked_subcommand is not None:
        return

    click.echo(context.get_help())
    context.exit(0)


@click.group(name="ai", cls=DgClickGroup)
def labs_ai_group() -> None:
    """Experimental AI-powered CLI commands."""


@click.group(name="scaffold", cls=DgClickGroup)
def labs_scaffold_group() -> None:
    """Experimental scaffolding commands."""


labs_ai_group.add_command(dispatch_command)
labs_scaffold_group.add_command(labs_scaffold_github_actions_ai_dispatch_command)
labs_group.add_command(labs_ai_group)
labs_group.add_command(labs_scaffold_group)

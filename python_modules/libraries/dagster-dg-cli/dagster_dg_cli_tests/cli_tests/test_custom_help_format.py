import textwrap

import click
from click.testing import CliRunner
from dagster_dg_core.utils import DgClickCommand, DgClickGroup, set_option_help_output_group
from dagster_test.dg_utils.utils import (
    ProxyRunner,
    assert_runner_result,
    fixed_panel_width,
    isolated_example_project_foo_bar,
    match_terminal_box_output,
)

# ########################
# ##### TEST CLI
# ########################

# The names of our global options are special-cased, so use one of them here (--verbose) as
# a test case.


@click.group(name="root", cls=DgClickGroup)
@click.option("--root-opt", type=str, default="root", help="Root option.")
@click.option("--verbose", type=str, default="test", help="Verbose output.")
def root(root_opt, verbose):
    """Root group."""
    pass


@root.group(name="sub-group", cls=DgClickGroup)
@click.option("--sub-group-opt", type=str, default="sub-group", help="Sub-group option.")
@click.option("--verbose", type=str, default="test", help="Verbose output.")
def sub_group(sub_group_opt, verbose):
    """Sub-group."""
    pass


@sub_group.command(name="sub-group-command", cls=DgClickCommand)
@click.option(
    "--sub-group-command-opt",
    type=str,
    default="sub_group_command",
    help="Sub-group-command option.",
)
@click.option("--verbose", type=str, default="test", help="Verbose output.")
def sub_group_command(sub_group_command_opt, verbose):
    """Sub-group-command."""
    pass


@root.group(name="sub-command", cls=DgClickGroup)
@click.option("--sub-command-opt", type=str, default="sub-command", help="Sub-command option.")
@click.option("--verbose", type=str, default="test", help="Verbose output.")
def sub_command(sub_command_opt, verbose):
    """Sub-command."""
    pass


for cmd in [root, sub_group, sub_group_command, sub_command]:
    # Make this a global option
    verbose_opt = next(p for p in cmd.params if p.name == "verbose")
    set_option_help_output_group(verbose_opt, "Global options")


# ########################
# ##### TESTS
# ########################


def test_root_help_message():
    runner = CliRunner()
    with fixed_panel_width():
        result = runner.invoke(root, ["--help"])
    assert_runner_result(result)

    assert match_terminal_box_output(
        result.output.strip(),
        textwrap.dedent("""
             Usage: root [OPTIONS] COMMAND [ARGS]...

             Root group.

            ╭─ Options ────────────────────────────────────────────────────────────────────╮
            │ --root-opt        TEXT  Root option.                                         │
            │ --help                  Show this message and exit.                          │
            ╰──────────────────────────────────────────────────────────────────────────────╯
            ╭─ Global options ─────────────────────────────────────────────────────────────╮
            │ --verbose        TEXT  Verbose output.                                       │
            ╰──────────────────────────────────────────────────────────────────────────────╯
            ╭─ Commands ───────────────────────────────────────────────────────────────────╮
            │ sub-command  Sub-command.                                                    │
            │ sub-group    Sub-group.                                                      │
            ╰──────────────────────────────────────────────────────────────────────────────╯
    """).strip(),
    )


def test_sub_group_with_option_help_message():
    runner = CliRunner()
    with fixed_panel_width():
        result = runner.invoke(root, ["sub-group", "--help"])
    assert_runner_result(result)
    assert match_terminal_box_output(
        result.output.strip(),
        textwrap.dedent("""
             Usage: root sub-group [OPTIONS] COMMAND [ARGS]...

             Sub-group.

            ╭─ Options ────────────────────────────────────────────────────────────────────╮
            │ --sub-group-opt        TEXT  Sub-group option.                               │
            │ --help                       Show this message and exit.                     │
            ╰──────────────────────────────────────────────────────────────────────────────╯
            ╭─ Global options ─────────────────────────────────────────────────────────────╮
            │ --verbose        TEXT  Verbose output.                                       │
            ╰──────────────────────────────────────────────────────────────────────────────╯
            ╭─ Commands ───────────────────────────────────────────────────────────────────╮
            │ sub-group-command  Sub-group-command.                                        │
            ╰──────────────────────────────────────────────────────────────────────────────╯
        """).strip(),
    )


def test_sub_group_command_with_option_help_message():
    runner = CliRunner()
    with fixed_panel_width():
        result = runner.invoke(root, ["sub-group", "sub-group-command", "--help"])
    assert_runner_result(result)
    assert match_terminal_box_output(
        result.output.strip(),
        textwrap.dedent("""
             Usage: root sub-group sub-group-command [OPTIONS]

             Sub-group-command.

            ╭─ Options ────────────────────────────────────────────────────────────────────╮
            │ --sub-group-command-opt        TEXT  Sub-group-command option.               │
            │ --help                               Show this message and exit.             │
            ╰──────────────────────────────────────────────────────────────────────────────╯
            ╭─ Global options ─────────────────────────────────────────────────────────────╮
            │ --verbose        TEXT  Verbose output.                                       │
            ╰──────────────────────────────────────────────────────────────────────────────╯
    """).strip(),
    )


def test_sub_command_with_option_help_message():
    runner = CliRunner()
    with fixed_panel_width():
        result = runner.invoke(root, ["sub-command", "--help"])
    assert_runner_result(result)
    assert match_terminal_box_output(
        result.output.strip(),
        textwrap.dedent("""
             Usage: root sub-command [OPTIONS] COMMAND [ARGS]...

             Sub-command.

            ╭─ Options ────────────────────────────────────────────────────────────────────╮
            │ --sub-command-opt        TEXT  Sub-command option.                           │
            │ --help                         Show this message and exit.                   │
            ╰──────────────────────────────────────────────────────────────────────────────╯
            ╭─ Global options ─────────────────────────────────────────────────────────────╮
            │ --verbose        TEXT  Verbose output.                                       │
            ╰──────────────────────────────────────────────────────────────────────────────╯
    """).strip(),
    )


def test_dynamic_subcommand_help_message():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
        with fixed_panel_width(width=120):
            result = runner.invoke(
                "scaffold", "defs", "dagster_test.components.SimplePipesScriptComponent", "--help"
            )
            assert_runner_result(result)
            assert match_terminal_box_output(
                result.output.strip(),
                textwrap.dedent("""
                Usage: dg scaffold defs [GLOBAL OPTIONS] dagster_test.components.SimplePipesScriptComponent [OPTIONS] DEFS_PATH

                A simple asset that runs a Python script with the Pipes subprocess client.                                             
                                                                                                                                        
                Because it is a pipes asset, no value is returned.

                ╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
                │ *    defs_path      TEXT  [required]                                                                                 │
                ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
                ╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
                │ --format               [yaml|python]  Format of the component configuration (yaml or python)                         │
                │ --json-params          TEXT           JSON string of scaffolder parameters. Mutually exclusive with passing          │
                │                                       individual parameters as options.                                              │
                │ --asset-key            TEXT           (scaffolder param) asset_key                                                   │
                │ --filename             TEXT           (scaffolder param) filename                                                    │
                │ --help         -h                     Show this message and exit.                                                    │
                ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
                ╭─ Global options ─────────────────────────────────────────────────────────────────────────────────────────────────────╮
                │ --verbose          Enable verbose output for debugging.                                                              │
                ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
                """).strip(),
            )

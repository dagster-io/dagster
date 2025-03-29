import textwrap

import click
from click.testing import CliRunner
from dagster_dg.utils import (
    DgClickCommand,
    DgClickGroup,
    ensure_dagster_dg_tests_import,
    set_option_help_output_group,
)

ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    fixed_panel_width,
    isolated_example_project_foo_bar,
    match_terminal_box_output,
)

# ########################
# ##### TEST CLI
# ########################

# The names of our global options are special-cased, so use one of them here (--disable-cache) as
# a test case.


@click.group(name="root", cls=DgClickGroup)
@click.option("--root-opt", type=str, default="root", help="Root option.")
@click.option("--disable-cache", type=str, default="test", help="Disable cache.")
def root(root_opt, disable_cache):
    """Root group."""
    pass


@root.group(name="sub-group", cls=DgClickGroup)
@click.option("--sub-group-opt", type=str, default="sub-group", help="Sub-group option.")
@click.option("--disable-cache", type=str, default="test", help="Disable cache.")
def sub_group(sub_group_opt, disable_cache):
    """Sub-group."""
    pass


@sub_group.command(name="sub-group-command", cls=DgClickCommand)
@click.option(
    "--sub-group-command-opt",
    type=str,
    default="sub_group_command",
    help="Sub-group-command option.",
)
@click.option("--disable-cache", type=str, default="test", help="Disable cache.")
def sub_group_command(sub_group_command_opt, disable_cache):
    """Sub-group-command."""
    pass


@root.group(name="sub-command", cls=DgClickGroup)
@click.option("--sub-command-opt", type=str, default="sub-command", help="Sub-command option.")
@click.option("--disable-cache", type=str, default="test", help="Disable cache.")
def sub_command(sub_command_opt, disable_cache):
    """Sub-command."""
    pass


for cmd in [root, sub_group, sub_group_command, sub_command]:
    # Make this a global option
    disable_cache_opt = next(p for p in cmd.params if p.name == "disable_cache")
    set_option_help_output_group(disable_cache_opt, "Global options")


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
            │ --disable-cache        TEXT  Disable cache.                                  │
            ╰──────────────────────────────────────────────────────────────────────────────╯
            ╭─ Commands ───────────────────────────────────────────────────────────────────╮
            │ sub-command   Sub-command.                                                   │
            │ sub-group     Sub-group.                                                     │
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
            │ --disable-cache        TEXT  Disable cache.                                  │
            ╰──────────────────────────────────────────────────────────────────────────────╯
            ╭─ Commands ───────────────────────────────────────────────────────────────────╮
            │ sub-group-command   Sub-group-command.                                       │
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
            │ --disable-cache        TEXT  Disable cache.                                  │
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
            │ --disable-cache        TEXT  Disable cache.                                  │
            ╰──────────────────────────────────────────────────────────────────────────────╯
    """).strip(),
    )


def test_dynamic_subcommand_help_message():
    with (
        ProxyRunner.test(use_fixed_test_components=True) as runner,
        isolated_example_project_foo_bar(runner),
    ):
        with fixed_panel_width(width=120):
            result = runner.invoke(
                "scaffold", "dagster_test.components.SimplePipesScriptComponent", "--help"
            )
            assert_runner_result(result)
            # Strip interpreter logging line
            output = "\n".join(result.output.split("\n")[1:])
        assert match_terminal_box_output(
            output.strip(),
            textwrap.dedent("""
Usage: dg scaffold [GLOBAL OPTIONS] dagster_test.components.SimplePipesScriptComponent [OPTIONS] INSTANCE_NAME

╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    instance_name      TEXT  [required]                                                                             │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --json-params          TEXT           JSON string of component parameters.                                           │
│ --format               [yaml|python]  Format of the component configuration (yaml or python)                         │
│ --asset-key            TEXT           asset_key                                                                      │
│ --filename             TEXT           filename                                                                       │
│ --help         -h                     Show this message and exit.                                                    │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Global options ─────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --cache-dir            TEXT  Specify a directory to use for the cache.                                               │
│ --disable-cache              Disable the cache..                                                                     │
│ --verbose                    Enable verbose output for debugging.                                                    │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
                            """).strip(),
        )

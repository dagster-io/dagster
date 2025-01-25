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
    isolated_example_code_location_foo_bar,
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


# Typer's rich help output is difficult to match exactly, as it contains blank lines with extraneous
# whitespace. So we use this helper function to compare the output of the help message with the
# expected output. Comparing line-by-line also helps debugging.
def _match_output(output: str, expected_output: str):
    output_lines = output.split("\n")
    expected_output_lines = expected_output.split("\n")
    for i in range(len(output_lines)):
        assert output_lines[i].strip() == expected_output_lines[i].strip()
    return True


def test_root_help_message():
    runner = CliRunner()
    result = runner.invoke(root, ["--help"])
    assert_runner_result(result)
    assert _match_output(
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
    result = runner.invoke(root, ["sub-group", "--help"])
    assert_runner_result(result)
    assert _match_output(
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
    result = runner.invoke(root, ["sub-group", "sub-group-command", "--help"])
    assert_runner_result(result)
    assert _match_output(
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
    result = runner.invoke(root, ["sub-command", "--help"])
    assert_runner_result(result)
    assert _match_output(
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
    with ProxyRunner.test() as runner, isolated_example_code_location_foo_bar(runner):
        result = runner.invoke(
            "component", "scaffold", "dagster_components.test.simple_pipes_script_asset", "--help"
        )
        assert _match_output(
            result.output.strip(),
            textwrap.dedent("""

                 Usage: dg component scaffold [GLOBAL OPTIONS] dagster_components.test.simple_pipes_script_asset [OPTIONS]              
                 COMPONENT_NAME                                                                                                         
                                                                                                                                        
                ╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
                │ *    component_name      TEXT  [required]                                                                            │
                ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
                ╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
                │ --json-params          TEXT  JSON string of component parameters.                                                    │
                │ --asset-key            TEXT  asset_key                                                                               │
                │ --filename             TEXT  filename                                                                                │
                │ --help         -h            Show this message and exit.                                                             │
                ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
                ╭─ Global options ─────────────────────────────────────────────────────────────────────────────────────────────────────╮
                │ --cache-dir                                                        PATH  Specify a directory to use for the cache.   │
                │ --disable-cache                                                          Disable the cache..                         │
                │ --verbose                                                                Enable verbose output for debugging.        │
                │ --builtin-component-lib                                            TEXT  Specify a builitin component library to     │
                │                                                                          use.                                        │
                │ --use-dg-managed-environment    --no-use-dg-managed-environment          Enable management of the virtual            │
                │                                                                          environment with uv.                        │
                ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
        """).strip(),
        )

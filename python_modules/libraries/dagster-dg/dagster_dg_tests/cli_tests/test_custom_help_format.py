import textwrap

import click
from click.testing import CliRunner
from dagster_dg.utils import DgClickCommand, DgClickGroup, ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import assert_runner_result

# ########################
# ##### TEST CLI
# ########################


@click.group(name="test", cls=DgClickGroup)
@click.option("--test-opt", type=str, default="test", help="Test option.")
def test_cli(test_opt):
    """Test CLI group."""
    pass


@test_cli.group(name="sub-test-1", cls=DgClickGroup)
@click.option("--sub-test-1-opt", type=str, default="sub-test-1", help="Sub-test 1 option.")
def sub_test_1(sub_test_1_opt):
    """Sub-test 1 group."""
    pass


@sub_test_1.command(name="alpha", cls=DgClickCommand)
@click.option("--alpha-opt", type=str, default="alpha", help="Alpha option.")
def alpha(alpha_opt):
    """Alpha command."""
    pass


@test_cli.group(name="sub-test-2", cls=DgClickGroup)
def sub_test_2():
    """Sub-test 2 group."""
    pass


@click.option("--beta-opt", type=str, default="alpha", help="Beta option.")
@sub_test_2.command(name="beta", cls=DgClickCommand)
def beta(beta_opt):
    """Beta command."""
    pass


@click.option("--delta-opt", type=str, default="delta", help="Delta option.")
@test_cli.command(name="delta", cls=DgClickCommand)
def delta(delta_opt):
    """Delta command."""
    pass


@test_cli.command(name="gamma", cls=DgClickCommand)
def gamma(gamma_opt):
    """Gamma command."""
    pass


# ########################
# ##### TESTS
# ########################


def test_root_group_help_message():
    runner = CliRunner()
    result = runner.invoke(test_cli, ["--help"])
    assert_runner_result(result)
    assert (
        result.output.strip()
        == textwrap.dedent("""
        Usage: test [OPTIONS] COMMAND [ARGS]...

          Test CLI group.

        Commands:
          delta       Delta command.
          gamma       Gamma command.
          sub-test-1  Sub-test 1 group.
          sub-test-2  Sub-test 2 group.

        Options:
          --test-opt TEXT  Test option.
          --help           Show this message and exit.
    """).strip()
    )


def test_sub_group_with_option_help_message():
    runner = CliRunner()
    result = runner.invoke(test_cli, ["sub-test-1", "--help"])
    assert_runner_result(result)
    assert (
        result.output.strip()
        == textwrap.dedent("""
        Usage: test [OPTIONS] sub-test-1 [OPTIONS] COMMAND [ARGS]...

          Sub-test 1 group.

        Commands:
          alpha  Alpha command.

        Options:
          --sub-test-1-opt TEXT  Sub-test 1 option.
          --help                 Show this message and exit.

        Options (test):
          --test-opt TEXT  Test option.
    """).strip()
    )


def test_command_in_sub_group_with_option_help_message():
    runner = CliRunner()
    result = runner.invoke(test_cli, ["sub-test-1", "alpha", "--help"])
    assert_runner_result(result)
    assert (
        result.output.strip()
        == textwrap.dedent("""
        Usage: test [OPTIONS] sub-test-1 [OPTIONS] alpha [OPTIONS]

          Alpha command.

        Options:
          --alpha-opt TEXT  Alpha option.
          --help            Show this message and exit.

        Options (test sub-test-1):
          --sub-test-1-opt TEXT  Sub-test 1 option.

        Options (test):
          --test-opt TEXT  Test option.
    """).strip()
    )


def test_sub_group_with_no_option_help_message():
    runner = CliRunner()
    result = runner.invoke(test_cli, ["sub-test-2", "--help"])
    assert_runner_result(result)
    assert (
        result.output.strip()
        == textwrap.dedent("""
        Usage: test [OPTIONS] sub-test-2 [OPTIONS] COMMAND [ARGS]...

          Sub-test 2 group.

        Commands:
          beta  Beta command.

        Options:
          --help  Show this message and exit.

        Options (test):
          --test-opt TEXT  Test option.
    """).strip()
    )


def test_command_in_sub_group_with_no_option_help_message():
    runner = CliRunner()
    result = runner.invoke(test_cli, ["sub-test-2", "beta", "--help"])
    assert_runner_result(result)
    assert (
        result.output.strip()
        == textwrap.dedent("""
        Usage: test [OPTIONS] sub-test-2 beta [OPTIONS]

          Beta command.

        Options:
          --beta-opt TEXT  Beta option.
          --help           Show this message and exit.

        Options (test):
          --test-opt TEXT  Test option.
    """).strip()
    )


def test_command_with_option_in_root_group_help_message():
    runner = CliRunner()
    result = runner.invoke(test_cli, ["delta", "--help"])
    assert_runner_result(result)
    assert (
        result.output.strip()
        == textwrap.dedent("""
        Usage: test [OPTIONS] delta [OPTIONS]

          Delta command.

        Options:
          --delta-opt TEXT  Delta option.
          --help            Show this message and exit.

        Options (test):
          --test-opt TEXT  Test option.
    """).strip()
    )


def test_command_with_no_option_in_root_group_help_message():
    runner = CliRunner()
    result = runner.invoke(test_cli, ["gamma", "--help"])
    assert_runner_result(result)
    assert (
        result.output.strip()
        == textwrap.dedent("""
        Usage: test [OPTIONS] gamma [OPTIONS]

          Gamma command.

        Options:
          --help  Show this message and exit.

        Options (test):
          --test-opt TEXT  Test option.
    """).strip()
    )

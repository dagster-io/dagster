import pytest
from click.testing import CliRunner
from dagster._cli.job import execute_print_command, job_print_command
from dagster._core.test_utils import instance_for_test
from dagster._utils import file_relative_path

from dagster_tests.cli_tests.command_tests.test_cli_commands import (
    launch_command_contexts,
    valid_remote_job_target_cli_args,
)


def no_print(_):
    return None


@pytest.mark.parametrize("gen_job_args", launch_command_contexts())
def test_print_command_verbose(gen_job_args):
    with gen_job_args as (cli_args, instance):
        execute_print_command(
            **cli_args,
            instance=instance,
            verbose=True,
            print_fn=no_print,
        )


@pytest.mark.parametrize("gen_job_args", launch_command_contexts())
def test_print_command(gen_job_args):
    with gen_job_args as (cli_args, instance):
        execute_print_command(
            **cli_args,
            instance=instance,
            verbose=False,
            print_fn=no_print,
        )


@pytest.mark.parametrize("job_cli_args", valid_remote_job_target_cli_args())
def test_job_print_command_cli(job_cli_args):
    with instance_for_test():
        runner = CliRunner()

        result = runner.invoke(job_print_command, job_cli_args)
        assert result.exit_code == 0, result.stdout

        result = runner.invoke(job_print_command, ["--verbose"] + job_cli_args)
        assert result.exit_code == 0, result.stdout


def test_print_command_baz():
    with instance_for_test():
        runner = CliRunner()

        res = runner.invoke(
            job_print_command,
            [
                "--verbose",
                "-f",
                file_relative_path(__file__, "test_cli_commands.py"),
                "-a",
                "bar",
                "-j",
                "quux_job",
            ],
        )
        assert res.exit_code == 0, res.stdout

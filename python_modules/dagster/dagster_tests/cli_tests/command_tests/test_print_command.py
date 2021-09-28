import pytest
from click.testing import CliRunner
from dagster.cli.job import job_print_command
from dagster.cli.pipeline import execute_print_command, pipeline_print_command
from dagster.core.test_utils import instance_for_test
from dagster.utils import file_relative_path

from .test_cli_commands import (
    launch_command_contexts,
    valid_external_job_target_cli_args,
    valid_external_pipeline_target_cli_args_no_preset,
)


def no_print(_):
    return None


@pytest.mark.parametrize("gen_pipeline_args", launch_command_contexts())
def test_print_command_verbose(gen_pipeline_args):
    with gen_pipeline_args as (cli_args, instance):
        execute_print_command(
            instance=instance,
            verbose=True,
            cli_args=cli_args,
            print_fn=no_print,
            using_job_op_graph_apis=False,
        )


@pytest.mark.parametrize("gen_pipeline_args", launch_command_contexts())
def test_print_command(gen_pipeline_args):
    with gen_pipeline_args as (cli_args, instance):
        execute_print_command(
            instance=instance,
            verbose=False,
            cli_args=cli_args,
            print_fn=no_print,
            using_job_op_graph_apis=False,
        )


@pytest.mark.parametrize("pipeline_cli_args", valid_external_pipeline_target_cli_args_no_preset())
def test_print_command_cli(pipeline_cli_args):
    with instance_for_test():

        runner = CliRunner()

        result = runner.invoke(pipeline_print_command, pipeline_cli_args)
        assert result.exit_code == 0, result.stdout

        result = runner.invoke(pipeline_print_command, ["--verbose"] + pipeline_cli_args)
        assert result.exit_code == 0, result.stdout


@pytest.mark.parametrize("job_cli_args", valid_external_job_target_cli_args())
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
            pipeline_print_command,
            [
                "--verbose",
                "-f",
                file_relative_path(__file__, "test_cli_commands.py"),
                "-a",
                "bar",
                "-p",
                "baz",
            ],
        )
        assert res.exit_code == 0, res.stdout

        res = runner.invoke(
            job_print_command,
            [
                "--verbose",
                "-f",
                file_relative_path(__file__, "test_cli_commands.py"),
                "-a",
                "bar",
                "-j",
                "baz",
            ],
        )
        assert res.exit_code == 0, res.stdout

import pytest
from click.testing import CliRunner

from dagster._cli.job import execute_scaffold_command, job_scaffold_command

from .test_cli_commands import (
    valid_job_python_origin_target_cli_args,
    valid_pipeline_or_job_python_origin_target_args,
)


def no_print(_):
    return None


@pytest.mark.parametrize("cli_args", valid_pipeline_or_job_python_origin_target_args())
def test_scaffold_command(cli_args):
    cli_args["print_only_required"] = True
    execute_scaffold_command(cli_args=cli_args, print_fn=no_print)

    cli_args["print_only_required"] = False
    execute_scaffold_command(cli_args=cli_args, print_fn=no_print)


@pytest.mark.parametrize("cli_args", valid_job_python_origin_target_cli_args())
def test_job_scaffold_command_cli(cli_args):
    runner = CliRunner()

    result = runner.invoke(job_scaffold_command, cli_args)
    assert result.exit_code == 0

    result = runner.invoke(job_scaffold_command, ["--print-only-required"] + cli_args)
    assert result.exit_code == 0

import click
import pytest
from click.testing import CliRunner
from dagster._cli.workspace.cli_target import get_remote_job_from_kwargs, job_target_argument
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation import RemoteJob
from dagster._core.test_utils import instance_for_test
from dagster._utils import file_relative_path


def load_pipeline_via_cli_runner(cli_args):
    capture_result = {"external_pipeline": None}

    @click.command(name="test_pipeline_command")
    @job_target_argument
    def command(**kwargs):
        with get_remote_job_from_kwargs(DagsterInstance.get(), "", kwargs) as remote_job:
            capture_result["external_pipeline"] = remote_job

    with instance_for_test():
        runner = CliRunner()
        result = runner.invoke(command, cli_args)

    remote_job = capture_result["external_pipeline"]
    return result, remote_job


def successfully_load_pipeline_via_cli(cli_args):
    result, remote_job = load_pipeline_via_cli_runner(cli_args)
    assert result.exit_code == 0, result
    assert isinstance(remote_job, RemoteJob)
    return remote_job


PYTHON_FILE_IN_NAMED_LOCATION_WORKSPACE = file_relative_path(
    __file__, "hello_world_in_file/python_file_with_named_location_workspace.yaml"
)


def get_all_loading_combos():
    def _iterate_combos():
        possible_location_args = [[], ["-l", "hello_world_location"]]
        possible_repo_args = [[], ["-r", "hello_world_repository"]]
        possible_job_args = [[], ["-j", "hello_world_job"]]

        for location_args in possible_location_args:
            for repo_args in possible_repo_args:
                for job_args in possible_job_args:
                    yield (
                        [
                            "-w",
                            PYTHON_FILE_IN_NAMED_LOCATION_WORKSPACE,
                        ]
                        + location_args
                        + repo_args
                        + job_args
                    )

    return tuple(_iterate_combos())


@pytest.mark.parametrize("cli_args", get_all_loading_combos())
def test_valid_loading_combos_single_job_code_location(cli_args):
    remote_job = successfully_load_pipeline_via_cli(cli_args)
    assert isinstance(remote_job, RemoteJob)
    assert remote_job.name == "hello_world_job"


def test_repository_target_argument_one_repo_and_specified_wrong():
    result, _ = load_pipeline_via_cli_runner(
        ["-w", PYTHON_FILE_IN_NAMED_LOCATION_WORKSPACE, "-j", "not_present"]
    )

    assert result.exit_code == 2
    assert (
        """Job "not_present" not found in repository """
        """"hello_world_repository". Found ['hello_world_job'] instead."""
    ) in result.stdout


MULTI_JOB_WORKSPACE = file_relative_path(__file__, "multi_job/multi_job.yaml")


def test_successfully_find_job():
    assert (
        successfully_load_pipeline_via_cli(["-w", MULTI_JOB_WORKSPACE, "-j", "job_one"]).name
        == "job_one"
    )

    assert (
        successfully_load_pipeline_via_cli(["-w", MULTI_JOB_WORKSPACE, "-j", "job_two"]).name
        == "job_two"
    )


def test_must_provide_name_to_multi_job():
    result, _ = load_pipeline_via_cli_runner(["-w", MULTI_JOB_WORKSPACE])

    assert result.exit_code == 2
    assert (
        """Must provide --job as there is more than one job in """
        """multi_job. Options are: ['job_one', 'job_two']."""
    ) in result.stdout

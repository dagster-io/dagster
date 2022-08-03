import click
import pytest
from click.testing import CliRunner

from dagster._cli.job import execute_launch_command, job_launch_command
from dagster._core.errors import DagsterRunAlreadyExists
from dagster._core.storage.pipeline_run import PipelineRunStatus
from dagster._core.test_utils import new_cwd
from dagster._utils import file_relative_path

from .test_cli_commands import (
    default_cli_test_instance,
    grpc_server_bar_cli_args,
    launch_command_contexts,
    memoizable_job,
    non_existant_python_origin_target_args,
    python_bar_cli_args,
    valid_external_job_target_cli_args,
)


def run_launch(kwargs, instance, expected_count=None):
    run = execute_launch_command(instance, kwargs)
    assert run
    if expected_count:
        assert instance.get_runs_count() == expected_count
    instance.run_launcher.join()


def run_launch_cli(execution_args, instance, expected_count=None):
    runner = CliRunner()
    result = runner.invoke(job_launch_command, execution_args)
    assert result.exit_code == 0, result.stdout
    if expected_count:
        assert instance.get_runs_count() == expected_count


def run_job_launch_cli(execution_args, instance, expected_count=None):
    runner = CliRunner()
    result = runner.invoke(job_launch_command, execution_args)
    assert result.exit_code == 0, result.stdout
    if expected_count:
        assert instance.get_runs_count() == expected_count


@pytest.mark.parametrize("gen_pipeline_args", launch_command_contexts())
def test_launch_pipeline(gen_pipeline_args):
    with gen_pipeline_args as (cli_args, instance):
        run_launch(cli_args, instance, expected_count=1)


def test_launch_non_existant_file():
    with default_cli_test_instance() as instance:
        kwargs = non_existant_python_origin_target_args()

        with pytest.raises(click.UsageError, match="Error loading location"):
            run_launch(kwargs, instance)


@pytest.mark.parametrize("job_cli_args", valid_external_job_target_cli_args())
def test_launch_job_cli(job_cli_args):
    with default_cli_test_instance() as instance:
        run_job_launch_cli(job_cli_args, instance, expected_count=1)


@pytest.mark.parametrize(
    "gen_pipeline_args",
    [python_bar_cli_args("qux", True), grpc_server_bar_cli_args("qux", True)],
)
def test_launch_with_run_id(gen_pipeline_args):
    runner = CliRunner()
    run_id = "my_super_cool_run_id"
    with default_cli_test_instance() as instance:
        with gen_pipeline_args as args:
            result = runner.invoke(
                job_launch_command,
                args
                + [
                    "--run-id",
                    run_id,
                ],
            )
            assert result.exit_code == 0

            run = instance.get_run_by_id(run_id)
            assert run is not None

            # running it again should fail since run_id has to be unique
            bad_result = runner.invoke(
                job_launch_command,
                args
                + [
                    "--run-id",
                    run_id,
                ],
            )
            assert bad_result.exit_code == 1
            assert isinstance(bad_result.exception, DagsterRunAlreadyExists)


@pytest.mark.parametrize(
    "gen_job_args",
    [python_bar_cli_args("qux", True), grpc_server_bar_cli_args("qux", True)],
)
def test_job_launch_with_run_id(gen_job_args):
    runner = CliRunner()
    run_id = "my_super_cool_run_id"
    with default_cli_test_instance() as instance:
        with gen_job_args as args:
            result = runner.invoke(
                job_launch_command,
                args
                + [
                    "--run-id",
                    run_id,
                ],
            )
            assert result.exit_code == 0

            run = instance.get_run_by_id(run_id)
            assert run is not None

            # running it again should fail since run_id has to be unique
            bad_result = runner.invoke(
                job_launch_command,
                args
                + [
                    "--run-id",
                    run_id,
                ],
            )
            assert bad_result.exit_code == 1
            assert isinstance(bad_result.exception, DagsterRunAlreadyExists)


@pytest.mark.parametrize(
    "gen_pipeline_args",
    [python_bar_cli_args("qux", True), grpc_server_bar_cli_args("qux", True)],
)
def test_launch_queued(gen_pipeline_args):
    runner = CliRunner()
    run_id = "my_super_cool_run_id"
    with default_cli_test_instance(
        overrides={
            "run_coordinator": {
                "class": "QueuedRunCoordinator",
                "module": "dagster._core.run_coordinator",
            }
        }
    ) as instance:
        with gen_pipeline_args as args:
            result = runner.invoke(
                job_launch_command,
                args
                + [
                    "--run-id",
                    run_id,
                ],
            )
            assert result.exit_code == 0

            run = instance.get_run_by_id(run_id)
            assert run is not None

            assert run.status == PipelineRunStatus.QUEUED


@pytest.mark.parametrize(
    "gen_pipeline_args",
    [python_bar_cli_args("qux", True), grpc_server_bar_cli_args("qux", True)],
)
def test_job_launch_queued(gen_pipeline_args):
    runner = CliRunner()
    run_id = "my_super_cool_run_id"
    with default_cli_test_instance(
        overrides={
            "run_coordinator": {
                "class": "QueuedRunCoordinator",
                "module": "dagster._core.run_coordinator",
            }
        }
    ) as instance:
        with gen_pipeline_args as args:
            result = runner.invoke(
                job_launch_command,
                args
                + [
                    "--run-id",
                    run_id,
                ],
            )
            assert result.exit_code == 0

            run = instance.get_run_by_id(run_id)
            assert run is not None

            assert run.status == PipelineRunStatus.QUEUED


def test_default_working_directory():
    runner = CliRunner()
    import os

    with default_cli_test_instance() as instance:
        with new_cwd(os.path.dirname(__file__)):
            result = runner.invoke(
                job_launch_command,
                [
                    "-f",
                    file_relative_path(__file__, "file_with_local_import.py"),
                    "-a",
                    "qux_job",
                ],
            )
            assert result.exit_code == 0
            runs = instance.get_runs()
            assert len(runs) == 1


def test_launch_using_memoization():
    runner = CliRunner()
    with default_cli_test_instance() as instance:
        with python_bar_cli_args("memoizable_job", True) as args:
            result = runner.invoke(job_launch_command, args + ["--run-id", "first"])
            assert result.exit_code == 0
            run = instance.get_run_by_id("first")

            # A None value of step_keys_to_execute indicates executing every step in the plan.
            assert len(run.step_keys_to_execute) == 1

            # Execute the pipeline to pretend that the launch went through and memoized some result.
            result = memoizable_job.execute_in_process(instance=instance)
            assert result.success

            result = runner.invoke(job_launch_command, args + ["--run-id", "second"])
            assert result.exit_code == 0
            run = instance.get_run_by_id("second")
            assert len(run.step_keys_to_execute) == 0


def test_job_launch_only_selects_job():
    job_kwargs = {
        "workspace": None,
        "pipeline_or_job": "my_job",
        "python_file": file_relative_path(__file__, "repo_pipeline_and_job.py"),
        "module_name": None,
        "attribute": "my_repo",
    }
    pipeline_kwargs = job_kwargs.copy()
    pipeline_kwargs["pipeline_or_job"] = "my_pipeline"

    with default_cli_test_instance() as instance:
        execute_launch_command(
            instance,
            job_kwargs,
            using_job_op_graph_apis=True,
        )

        with pytest.raises(Exception, match="not found in repository"):
            execute_launch_command(instance, pipeline_kwargs, using_job_op_graph_apis=True)

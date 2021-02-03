import pytest
from click.testing import CliRunner
from dagster.cli.pipeline import execute_launch_command, pipeline_launch_command
from dagster.core.errors import DagsterRunAlreadyExists, DagsterUserCodeProcessError
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.test_utils import new_cwd
from dagster.utils import file_relative_path

from .test_cli_commands import (
    default_cli_test_instance,
    grpc_server_bar_cli_args,
    launch_command_contexts,
    non_existant_python_origin_target_args,
    python_bar_cli_args,
    valid_external_pipeline_target_cli_args_with_preset,
)


def run_launch(kwargs, instance, expected_count=None):
    run = execute_launch_command(instance, kwargs)
    assert run
    if expected_count:
        assert instance.get_runs_count() == expected_count
    instance.run_launcher.join()


def run_launch_cli(execution_args, instance, expected_count=None):
    runner = CliRunner()
    result = runner.invoke(pipeline_launch_command, execution_args)
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

        with pytest.raises(DagsterUserCodeProcessError):
            run_launch(kwargs, instance)


@pytest.mark.parametrize("pipeline_cli_args", valid_external_pipeline_target_cli_args_with_preset())
def test_launch_pipeline_cli(pipeline_cli_args):
    with default_cli_test_instance() as instance:
        run_launch_cli(pipeline_cli_args, instance, expected_count=1)


@pytest.mark.parametrize(
    "gen_pipeline_args",
    [
        python_bar_cli_args("foo"),
        grpc_server_bar_cli_args("foo"),
    ],
)
def test_launch_subset_pipeline_single_clause_solid_name(gen_pipeline_args):
    runner = CliRunner()
    with default_cli_test_instance() as instance:
        with gen_pipeline_args as args:
            result = runner.invoke(
                pipeline_launch_command,
                args
                + [
                    "--solid-selection",
                    "do_something",
                ],
            )
            assert result.exit_code == 0
            runs = instance.get_runs()
            assert len(runs) == 1
            run = runs[0]
            assert run.solid_selection == ["do_something"]
            assert run.solids_to_execute == {"do_something"}


@pytest.mark.parametrize(
    "gen_pipeline_args",
    [
        python_bar_cli_args("foo"),
        grpc_server_bar_cli_args("foo"),
    ],
)
def test_launch_subset_pipeline_single_clause_dsl_query(gen_pipeline_args):
    runner = CliRunner()
    with default_cli_test_instance() as instance:
        with gen_pipeline_args as args:
            result = runner.invoke(
                pipeline_launch_command,
                args
                + [
                    "--solid-selection",
                    "*do_something+",
                ],
            )
            assert result.exit_code == 0
            runs = instance.get_runs()
            assert len(runs) == 1
            run = runs[0]
            assert run.solid_selection == ["*do_something+"]
            assert run.solids_to_execute == {"do_something", "do_input"}


@pytest.mark.parametrize(
    "gen_pipeline_args",
    [
        python_bar_cli_args("foo"),
        grpc_server_bar_cli_args("foo"),
    ],
)
def test_launch_subset_pipeline_multiple_clauses(gen_pipeline_args):
    runner = CliRunner()
    with default_cli_test_instance() as instance:
        with gen_pipeline_args as args:
            result = runner.invoke(
                pipeline_launch_command,
                args
                + [
                    "--solid-selection",
                    "*do_something+,do_input",
                ],
            )
            assert result.exit_code == 0
            runs = instance.get_runs()
            assert len(runs) == 1
            run = runs[0]
            assert set(run.solid_selection) == set(["*do_something+", "do_input"])
            assert run.solids_to_execute == {"do_something", "do_input"}


@pytest.mark.parametrize(
    "gen_pipeline_args",
    [python_bar_cli_args("foo"), grpc_server_bar_cli_args("foo")],
)
def test_launch_subset_pipeline_invalid_value(gen_pipeline_args):
    runner = CliRunner()
    with default_cli_test_instance() as _instance:
        with gen_pipeline_args as args:
            result = runner.invoke(
                pipeline_launch_command,
                args
                + [
                    "--solid-selection",
                    "a, b",
                ],
            )
            assert result.exit_code == 1
            assert "No qualified solids to execute found for solid_selection" in str(
                result.exception
            )


@pytest.mark.parametrize(
    "gen_pipeline_args",
    [python_bar_cli_args("foo"), grpc_server_bar_cli_args("foo")],
)
def test_launch_with_run_id(gen_pipeline_args):
    runner = CliRunner()
    run_id = "my_super_cool_run_id"
    with default_cli_test_instance() as instance:
        with gen_pipeline_args as args:
            result = runner.invoke(
                pipeline_launch_command,
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
                pipeline_launch_command,
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
    [python_bar_cli_args("foo"), grpc_server_bar_cli_args("foo")],
)
def test_launch_queued(gen_pipeline_args):
    runner = CliRunner()
    run_id = "my_super_cool_run_id"
    with default_cli_test_instance(
        overrides={
            "run_coordinator": {
                "class": "QueuedRunCoordinator",
                "module": "dagster.core.run_coordinator",
            }
        }
    ) as instance:
        with gen_pipeline_args as args:
            result = runner.invoke(
                pipeline_launch_command,
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


def test_empty_working_directory():
    runner = CliRunner()
    import os

    with default_cli_test_instance() as instance:
        with new_cwd(os.path.dirname(__file__)):
            result = runner.invoke(
                pipeline_launch_command,
                [
                    "-f",
                    file_relative_path(__file__, "file_with_local_import.py"),
                    "-a",
                    "foo_pipeline",
                ],
            )
            assert result.exit_code == 0
            runs = instance.get_runs()
            assert len(runs) == 1

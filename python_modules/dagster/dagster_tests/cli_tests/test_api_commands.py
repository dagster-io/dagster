import pytest
from click.testing import CliRunner
from dagster.cli import api
from dagster.cli.api import ExecuteRunArgs, ExecuteStepArgs
from dagster.core.instance import DagsterInstance
from dagster.core.test_utils import create_run_for_test, instance_for_test
from dagster.serdes import serialize_dagster_namedtuple
from dagster_tests.api_tests.utils import get_foo_pipeline_handle


def runner_execute_run_with_structured_logs(runner, cli_args):
    result = runner.invoke(api.execute_run_with_structured_logs_command, cli_args)
    if result.exit_code != 0:
        # CliRunner captures stdout so printing it out here
        raise Exception(
            (
                "dagster runner_execute_run_with_structured_logs commands with cli_args {cli_args} "
                'returned exit_code {exit_code} with stdout:\n"{stdout}"'
                '\n exception: "\n{exception}"'
                '\n and result as string: "{result}"'
            ).format(
                cli_args=cli_args,
                exit_code=result.exit_code,
                stdout=result.stdout,
                exception=result.exception,
                result=result,
            )
        )
    return result


@pytest.mark.parametrize(
    "pipeline_handle", [get_foo_pipeline_handle()],
)
def test_execute_run_with_structured_logs(pipeline_handle):
    runner = CliRunner()

    with instance_for_test(
        overrides={
            "compute_logs": {
                "module": "dagster.core.storage.noop_compute_log_manager",
                "class": "NoOpComputeLogManager",
            }
        }
    ) as instance:
        instance = DagsterInstance.get()
        run = create_run_for_test(instance, pipeline_name="foo", run_id="new_run")

        input_json = serialize_dagster_namedtuple(
            ExecuteRunArgs(
                pipeline_origin=pipeline_handle.get_origin(),
                pipeline_run_id=run.run_id,
                instance_ref=instance.get_ref(),
            )
        )

        result = runner_execute_run_with_structured_logs(runner, [input_json],)

    assert "PIPELINE_SUCCESS" in result.stdout, "no match, result: {}".format(result)


def runner_execute_step_with_structured_logs(runner, cli_args):
    result = runner.invoke(api.execute_step_with_structured_logs_command, cli_args)
    if result.exit_code != 0:
        # CliRunner captures stdout so printing it out here
        raise Exception(
            (
                "dagster runner_execute_step_with_structured_logs commands with cli_args {cli_args} "
                'returned exit_code {exit_code} with stdout:\n"{stdout}"'
                '\n exception: "\n{exception}"'
                '\n and result as string: "{result}"'
            ).format(
                cli_args=cli_args,
                exit_code=result.exit_code,
                stdout=result.stdout,
                exception=result.exception,
                result=result,
            )
        )
    return result


@pytest.mark.parametrize("pipeline_handle", [get_foo_pipeline_handle()])
def test_execute_step_with_structured_logs(pipeline_handle):
    runner = CliRunner()

    with instance_for_test(
        overrides={
            "compute_logs": {
                "module": "dagster.core.storage.noop_compute_log_manager",
                "class": "NoOpComputeLogManager",
            }
        }
    ) as instance:
        run = create_run_for_test(instance, pipeline_name="foo", run_id="new_run")

        input_json = serialize_dagster_namedtuple(
            ExecuteStepArgs(
                pipeline_origin=pipeline_handle.get_origin(),
                pipeline_run_id=run.run_id,
                instance_ref=instance.get_ref(),
            )
        )

        result = runner_execute_step_with_structured_logs(runner, [input_json],)

    assert "STEP_SUCCESS" in result.stdout

import mock
from click.testing import CliRunner
from dagster_tests.api_tests.utils import get_bar_repo_handle, get_foo_pipeline_handle

from dagster.cli import api
from dagster.cli.api import ExecuteRunArgs, ExecuteStepArgs, verify_step
from dagster.core.execution.plan.state import KnownExecutionState
from dagster.core.execution.retries import RetryState
from dagster.core.execution.stats import RunStepKeyStatsSnapshot
from dagster.core.host_representation import PipelineHandle
from dagster.core.instance import DagsterInstance
from dagster.core.test_utils import create_run_for_test, instance_for_test
from dagster.serdes import serialize_dagster_namedtuple


def runner_execute_run(runner, cli_args):
    result = runner.invoke(api.execute_run_command, cli_args)
    if result.exit_code != 0:
        # CliRunner captures stdout so printing it out here
        raise Exception(
            (
                "dagster runner_execute_run commands with cli_args {cli_args} "
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


def test_execute_run():
    with get_foo_pipeline_handle() as pipeline_handle:
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
                    pipeline_origin=pipeline_handle.get_python_origin(),
                    pipeline_run_id=run.run_id,
                    instance_ref=instance.get_ref(),
                )
            )

            result = runner_execute_run(
                runner,
                [input_json],
            )

            assert "PIPELINE_SUCCESS" in result.stdout, "no match, result: {}".format(result.stdout)

            # Framework errors (e.g. running a run that has already run) still result in a non-zero error code
            result = runner.invoke(api.execute_run_command, [input_json])
            assert result.exit_code == 0


def test_execute_run_fail_pipeline():
    with get_bar_repo_handle() as repo_handle:
        pipeline_handle = PipelineHandle("fail", repo_handle)
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
                    pipeline_origin=pipeline_handle.get_python_origin(),
                    pipeline_run_id=run.run_id,
                    instance_ref=instance.get_ref(),
                )
            )

            result = runner_execute_run(
                runner,
                [input_json],
            )
            assert result.exit_code == 0

            assert "RUN_FAILURE" in result.stdout, "no match, result: {}".format(result)

            run = create_run_for_test(
                instance, pipeline_name="foo", run_id="new_run_raise_on_error"
            )

            input_json_raise_on_failure = serialize_dagster_namedtuple(
                ExecuteRunArgs(
                    pipeline_origin=pipeline_handle.get_python_origin(),
                    pipeline_run_id=run.run_id,
                    instance_ref=instance.get_ref(),
                    set_exit_code_on_failure=True,
                )
            )

            result = runner.invoke(api.execute_run_command, [input_json_raise_on_failure])

            assert result.exit_code != 0, str(result.stdout)

            assert "RUN_FAILURE" in result.stdout, "no match, result: {}".format(result)

            # Framework errors (e.g. running a run that has already run) also result in a non-zero error code
            result = runner.invoke(api.execute_run_command, [input_json_raise_on_failure])
            assert result.exit_code != 0, str(result.stdout)


def test_execute_run_cannot_load():
    with get_foo_pipeline_handle() as pipeline_handle:
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

            input_json = serialize_dagster_namedtuple(
                ExecuteRunArgs(
                    pipeline_origin=pipeline_handle.get_python_origin(),
                    pipeline_run_id="FOOBAR",
                    instance_ref=instance.get_ref(),
                )
            )

            result = runner.invoke(
                api.execute_run_command,
                [input_json],
            )

            assert result.exit_code != 0

            assert "Pipeline run with id 'FOOBAR' not found for run execution" in str(
                result.exception
            ), "no match, result: {}".format(result.stdout)


def runner_execute_step(runner, cli_args):
    result = runner.invoke(api.execute_step_command, cli_args)
    if result.exit_code != 0:
        # CliRunner captures stdout so printing it out here
        raise Exception(
            (
                "dagster runner_execute_step commands with cli_args {cli_args} "
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


def test_execute_step():
    with get_foo_pipeline_handle() as pipeline_handle:
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
                    pipeline_origin=pipeline_handle.get_python_origin(),
                    pipeline_run_id=run.run_id,
                    step_keys_to_execute=None,
                    instance_ref=instance.get_ref(),
                )
            )

            result = runner_execute_step(
                runner,
                [input_json],
            )

        assert "STEP_SUCCESS" in result.stdout


def test_execute_step_1():
    with get_foo_pipeline_handle() as pipeline_handle:
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
                    pipeline_origin=pipeline_handle.get_python_origin(),
                    pipeline_run_id=run.run_id,
                    step_keys_to_execute=None,
                    instance_ref=instance.get_ref(),
                )
            )

            result = runner_execute_step(
                runner,
                [input_json],
            )

        assert "STEP_SUCCESS" in result.stdout


def test_execute_step_verify_step():
    with get_foo_pipeline_handle() as pipeline_handle:
        runner = CliRunner()

        with instance_for_test(
            overrides={
                "compute_logs": {
                    "module": "dagster.core.storage.noop_compute_log_manager",
                    "class": "NoOpComputeLogManager",
                }
            }
        ) as instance:
            run = create_run_for_test(
                instance,
                pipeline_name="foo",
                run_id="new_run",
            )

            input_json = serialize_dagster_namedtuple(
                ExecuteStepArgs(
                    pipeline_origin=pipeline_handle.get_python_origin(),
                    pipeline_run_id=run.run_id,
                    step_keys_to_execute=None,
                    instance_ref=instance.get_ref(),
                )
            )

            # Check that verify succeeds for step that has hasn't been fun (case 3)
            retries = RetryState()
            assert verify_step(instance, run, retries, step_keys_to_execute=["do_something"])

            # Check that verify fails when trying to retry with no original attempt (case 3)
            retries = RetryState()
            retries.mark_attempt("do_something")
            assert not verify_step(instance, run, retries, step_keys_to_execute=["do_something"])

            # Test trying to re-run a retry fails verify_step (case 2)
            with mock.patch("dagster.cli.api.get_step_stats_by_key") as _step_stats_by_key:
                _step_stats_by_key.return_value = {
                    "do_something": RunStepKeyStatsSnapshot(
                        run_id=run.run_id, step_key="do_something", attempts=2
                    )
                }

                retries = RetryState()
                retries.mark_attempt("do_something")
                assert not verify_step(
                    instance, run, retries, step_keys_to_execute=["do_something"]
                )

            runner_execute_step(
                runner,
                [input_json],
            )

            # # Check that verify fails for step that has already run (case 1)
            retries = RetryState()
            assert not verify_step(instance, run, retries, step_keys_to_execute=["do_something"])


@mock.patch("dagster.cli.api.verify_step")
def test_execute_step_verify_step_framework_error(mock_verify_step):
    with get_foo_pipeline_handle() as pipeline_handle:
        runner = CliRunner()

        mock_verify_step.side_effect = Exception("Unexpected framework error text")

        with instance_for_test(
            overrides={
                "compute_logs": {
                    "module": "dagster.core.storage.noop_compute_log_manager",
                    "class": "NoOpComputeLogManager",
                }
            }
        ) as instance:
            run = create_run_for_test(
                instance,
                pipeline_name="foo",
                run_id="new_run",
            )

            input_json = serialize_dagster_namedtuple(
                ExecuteStepArgs(
                    pipeline_origin=pipeline_handle.get_python_origin(),
                    pipeline_run_id=run.run_id,
                    step_keys_to_execute=["fake_step"],
                    instance_ref=instance.get_ref(),
                    should_verify_step=True,
                    known_state=KnownExecutionState(
                        {},
                        {
                            "blah": {"result": ["0", "1", "2"]},
                        },
                    ),
                )
            )
            result = runner.invoke(api.execute_step_command, [input_json])

            assert result.exit_code != 0

            # Framework error logged to event log
            logs = instance.all_logs(run.run_id)

            log_entry = logs[0]
            assert (
                log_entry.message
                == "An exception was thrown during step execution that is likely a framework error, rather than an error in user code."
            )
            assert log_entry.step_key == "fake_step"

            assert "Unexpected framework error text" in str(
                log_entry.dagster_event.event_specific_data.error
            )

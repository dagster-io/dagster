import sys
import time
from contextlib import contextmanager

import mock
import pytest
from click.testing import CliRunner
from dagster import job, op, repository
from dagster.cli import api
from dagster.cli.api import ExecuteRunArgs, ExecuteStepArgs, verify_step
from dagster.core.errors import DagsterExecutionInterruptedError
from dagster.core.execution.retries import RetryState
from dagster.core.execution.stats import RunStepKeyStatsSnapshot
from dagster.core.host_representation import (
    ManagedGrpcPythonEnvRepositoryLocationOrigin,
    PipelineHandle,
)
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.test_utils import create_run_for_test, instance_for_test
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.serdes import serialize_dagster_namedtuple
from dagster_tests.api_tests.utils import get_foo_pipeline_handle


@op
def slow_op():
    time.sleep(10)


@job
def slow_job():
    slow_op()


@repository
def my_repo():
    return [slow_job]


@contextmanager
def get_my_repo_repository_location():
    loadable_target_origin = LoadableTargetOrigin(
        executable_path=sys.executable,
        python_file=__file__,
        attribute="my_repo",
    )
    location_name = "my_repo_location"

    origin = ManagedGrpcPythonEnvRepositoryLocationOrigin(loadable_target_origin, location_name)

    with origin.create_test_location() as location:
        yield location


@contextmanager
def get_my_repo_handle():
    with get_my_repo_repository_location() as location:
        yield location.get_repository("my_repo").handle


@contextmanager
def get_slow_job_handle():
    with get_my_repo_handle() as repo_handle:
        yield PipelineHandle("slow_job", repo_handle)


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

        assert "PIPELINE_SUCCESS" in result.stdout, "no match, result: {}".format(result)


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
                    step_keys_to_execute=["do_something"],
                    instance_ref=instance.get_ref(),
                )
            )

            result = runner_execute_step(
                runner,
                [input_json],
            )

        assert "STEP_SUCCESS" in result.stdout


def test_execute_step_cancelation_no_cancel():
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
                    step_keys_to_execute=["do_something"],
                    instance_ref=instance.get_ref(),
                    self_managed_cancellation=True,
                )
            )

            result = runner_execute_step(
                runner,
                [input_json],
            )

        assert "STEP_SUCCESS" in result.stdout


def test_execute_step_cancelation_with_cancel():
    with get_slow_job_handle() as pipeline_handle:
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
                instance, pipeline_name="foo", run_id="new_run", status=PipelineRunStatus.CANCELING
            )

            input_json = serialize_dagster_namedtuple(
                ExecuteStepArgs(
                    pipeline_origin=pipeline_handle.get_python_origin(),
                    pipeline_run_id=run.run_id,
                    step_keys_to_execute=["slow_op"],
                    instance_ref=instance.get_ref(),
                    self_managed_cancellation=True,
                )
            )

            with pytest.raises(DagsterExecutionInterruptedError):
                runner_execute_step(
                    runner,
                    [input_json],
                )

            run = create_run_for_test(
                instance, pipeline_name="foo", run_id="newer_run", status=PipelineRunStatus.CANCELED
            )

            input_json = serialize_dagster_namedtuple(
                ExecuteStepArgs(
                    pipeline_origin=pipeline_handle.get_python_origin(),
                    pipeline_run_id=run.run_id,
                    step_keys_to_execute=["slow_op"],
                    instance_ref=instance.get_ref(),
                    self_managed_cancellation=True,
                )
            )

            with pytest.raises(DagsterExecutionInterruptedError):
                runner_execute_step(
                    runner,
                    [input_json],
                )


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
                    step_keys_to_execute=["do_something"],
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

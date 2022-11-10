# pylint: disable=unused-argument
import subprocess

from mock import MagicMock

from dagster import OpExecutionContext, RetryRequested, executor, job, op, reconstructable
from dagster._config import Permissive
from dagster._core.definitions.executor_definition import multiple_process_executor_requirements
from dagster._core.execution.api import execute_pipeline
from dagster._core.execution.retries import RetryMode
from dagster._core.executor.step_delegating import (
    CheckStepHealthResult,
    StepDelegatingExecutor,
    StepHandler,
)
from dagster._core.test_utils import instance_for_test
from dagster._utils import merge_dicts


class TestStepHandler(StepHandler):
    launched_first_attempt = False
    launched_second_attempt = False

    @property
    def name(self):
        return "TestStepHandler"

    def launch_step(self, step_handler_context):
        TestStepHandler.launch_step_count += 1
        assert step_handler_context.execute_step_args.step_keys_to_execute == ["retry_op"]

        print("TestStepHandler Launching Step!")  # pylint: disable=print-call
        TestStepHandler.processes.append(
            subprocess.Popen(step_handler_context.execute_step_args.get_command_args())
        )
        return iter(())

    def check_step_health(self, step_handler_context) -> CheckStepHealthResult:
        TestStepHandler.check_step_health_count += 1

        assert step_handler_context.execute_step_args.step_keys_to_execute == ["retry_op"]

        if step_handler_context.execute_step_args.known_state.get_retry_state().get_attempt_count(
                "retry_op"
            ) == 1:
            assert TestStepHandler.

        return CheckStepHealthResult.healthy()

    def terminate_step(self, step_handler_context):
        raise NotImplementedError()

    @classmethod
    def reset(cls):
        cls.processes = []
        cls.launch_step_count = 0
        cls.check_step_health_count = 0
        cls.terminate_step_count = 0
        cls.verify_step_count = 0

    @classmethod
    def wait_for_processes(cls):
        for p in cls.processes:
            p.wait(timeout=5)


@executor(
    name="mocked_executor",
    requirements=multiple_process_executor_requirements(),
    config_schema=Permissive(),
)
def mocked_executor(exc_init):
    return StepDelegatingExecutor(
        TestStepHandler(),
        **(merge_dicts({"retries": RetryMode.ENABLED}, exc_init.executor_config)),
        check_step_health_interval_seconds=0,
    )


@op
def retry_op(context: OpExecutionContext):
    if not context.retry_number:
        raise RetryRequested(seconds_to_wait=30)


@job(executor_def=mocked_executor)
def retry_job():
    retry_op()


def test_mocked_executor():
    TestStepHandler.reset()
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(retry_job),
            instance=instance,
            run_config={"execution": {"config": {}}},
        )
        TestStepHandler.wait_for_processes()

    assert result.success
    assert TestStepHandler.launch_step_count == 2

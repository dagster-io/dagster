# pylint: disable=unused-argument
import subprocess

import dagster._check as check
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
from dagster._utils.merger import merge_dicts


class TestStepHandler(StepHandler):
    launched_first_attempt = False
    launched_second_attempt = False
    processes = []

    @property
    def name(self):
        return "TestStepHandler"

    def launch_step(self, step_handler_context):
        assert step_handler_context.execute_step_args.step_keys_to_execute == ["retry_op"]

        known_state = check.not_none(step_handler_context.execute_step_args.known_state)
        attempt_count = known_state.get_retry_state().get_attempt_count("retry_op")
        if attempt_count == 0:
            assert TestStepHandler.launched_first_attempt is False
            assert TestStepHandler.launched_second_attempt is False
            TestStepHandler.launched_first_attempt = True
        elif attempt_count == 1:
            assert TestStepHandler.launched_first_attempt is True
            assert TestStepHandler.launched_second_attempt is False
            TestStepHandler.launched_second_attempt = True
        else:
            raise Exception("Unexpected attempt count")

        print("TestStepHandler Launching Step!")  # noqa: T201
        TestStepHandler.processes.append(
            subprocess.Popen(step_handler_context.execute_step_args.get_command_args())
        )
        return iter(())

    def check_step_health(self, step_handler_context) -> CheckStepHealthResult:
        assert step_handler_context.execute_step_args.step_keys_to_execute == ["retry_op"]

        known_state = check.not_none(step_handler_context.execute_step_args.known_state)
        attempt_count = known_state.get_retry_state().get_attempt_count("retry_op")
        if attempt_count == 0:
            assert TestStepHandler.launched_first_attempt is True
            assert TestStepHandler.launched_second_attempt is False
        elif attempt_count == 1:
            assert TestStepHandler.launched_first_attempt is True
            assert (
                TestStepHandler.launched_second_attempt
            ), "Second attempt not launched, shouldn't be checking on it"

        return CheckStepHealthResult.healthy()

    def terminate_step(self, step_handler_context):
        raise NotImplementedError()

    @classmethod
    def reset(cls):
        cls.launched_first_attempt = False
        cls.launched_second_attempt = False

    @classmethod
    def wait_for_processes(cls):
        for p in cls.processes:
            p.wait(timeout=5)


@executor(
    name="retry_assertion_executor",
    requirements=multiple_process_executor_requirements(),
    config_schema=Permissive(),
)
def retry_assertion_executor(exc_init):
    return StepDelegatingExecutor(
        TestStepHandler(),
        **(merge_dicts({"retries": RetryMode.ENABLED}, exc_init.executor_config)),
        check_step_health_interval_seconds=0,
    )


@op(config_schema={"fails_before_pass": int})
def retry_op(context: OpExecutionContext):
    if context.retry_number < context.op_config["fails_before_pass"]:
        # enough for check_step_health to be called, since we set check_step_health_interval_seconds=0
        raise RetryRequested(seconds_to_wait=5)


@job(executor_def=retry_assertion_executor)
def retry_job():
    retry_op()


def test_retries_no_check_step_health_during_wait():
    TestStepHandler.reset()
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(retry_job),
            instance=instance,
            run_config={
                "execution": {"config": {}},
                "ops": {"retry_op": {"config": {"fails_before_pass": 1}}},
            },
        )
        TestStepHandler.wait_for_processes()
    assert result.success


def test_retries_exhausted():
    TestStepHandler.reset()
    with instance_for_test() as instance:
        result = execute_pipeline(
            reconstructable(retry_job),
            instance=instance,
            run_config={
                "execution": {"config": {}},
                "ops": {"retry_op": {"config": {"fails_before_pass": 2}}},
            },
        )
        TestStepHandler.wait_for_processes()
    assert not result.success
    assert not [
        e
        for e in result.event_list
        if "Attempted to mark step retry_op as complete that was not known to be in flight"
        in str(e)
    ]

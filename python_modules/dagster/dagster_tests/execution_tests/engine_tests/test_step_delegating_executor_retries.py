import os
import subprocess
import tempfile

import dagster._check as check
from dagster import OpExecutionContext, RetryRequested, executor, job, op, reconstructable
from dagster._config import Permissive
from dagster._config.pythonic_config.resource import ConfigurableResource
from dagster._core.definitions.executor_definition import multiple_process_executor_requirements
from dagster._core.definitions.policy import RetryPolicy
from dagster._core.execution.api import execute_job
from dagster._core.execution.context.init import InitResourceContext
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
            assert TestStepHandler.launched_second_attempt, (
                "Second attempt not launched, shouldn't be checking on it"
            )

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
        with execute_job(
            reconstructable(retry_job),
            instance=instance,
            run_config={
                "execution": {"config": {}},
                "ops": {"retry_op": {"config": {"fails_before_pass": 1}}},
            },
        ) as result:
            TestStepHandler.wait_for_processes()
            assert result.success


def test_retries_exhausted():
    TestStepHandler.reset()
    with instance_for_test() as instance:
        with execute_job(
            reconstructable(retry_job),
            instance=instance,
            run_config={
                "execution": {"config": {}},
                "ops": {"retry_op": {"config": {"fails_before_pass": 2}}},
            },
        ) as result:
            TestStepHandler.wait_for_processes()
            assert not result.success
            assert not [
                e
                for e in result.all_events
                if "Attempted to mark step retry_op as complete that was not known to be in flight"
                in str(e)
            ]


class FailOnceResource(ConfigurableResource):
    parent_dir: str

    def create_resource(self, context: InitResourceContext) -> None:
        filepath = os.path.join(self.parent_dir, f"{context.run_id}_resource.txt")
        if not os.path.exists(filepath):
            open(filepath, "a", encoding="utf8").close()
            raise ValueError("Resource error")


@op(retry_policy=RetryPolicy(max_retries=3))
def resource_op(my_resource: FailOnceResource):
    pass


@job(resource_defs={"my_resource": FailOnceResource(parent_dir="")})
def resource_fail_once_job():
    resource_op()


def test_resource_retries():
    TestStepHandler.reset()
    with tempfile.TemporaryDirectory() as tempdir:
        with instance_for_test() as instance:
            with execute_job(
                reconstructable(resource_fail_once_job),
                instance=instance,
                run_config={"resources": {"my_resource": {"config": {"parent_dir": tempdir}}}},
            ) as result:
                TestStepHandler.wait_for_processes()
                assert result.success
                step_events = result.events_for_node("resource_op")
                assert len([event for event in step_events if event.is_step_up_for_retry]) == 1

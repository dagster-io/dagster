import subprocess
from typing import Iterator, Optional

from dagster import Definitions, job, op, reconstructable
from dagster._core.events import DagsterEvent
from dagster._core.execution.api import execute_job
from dagster._core.execution.context.system import IStepContext
from dagster._core.execution.retries import RetryMode
from dagster._core.executor.multi_environment.multi_environment_step_handler import (
    MultiEnvironmentExecutor,
    RemoteEnvironmentSingleStepHandler,
)
from dagster._core.executor.step_delegating import (
    CheckStepHealthResult,
)
from dagster._core.executor.step_delegating.step_handler.base import (
    StepHandlerContext,
)
from dagster._core.test_utils import instance_for_test


class ProcessCollection:
    processes = []  # type: ignore

    @classmethod
    def reset(cls):
        cls.processes = []

    @classmethod
    def wait_for_processes(cls):
        for p in cls.processes:
            p.wait(timeout=5)


class OutOfProcessSingleStepHandlerForTest(RemoteEnvironmentSingleStepHandler):
    def launch_single_step(
        self, step_context: IStepContext, step_handler_context: StepHandlerContext
    ) -> Optional[Iterator[DagsterEvent]]:
        ProcessCollection.processes.append(
            subprocess.Popen(step_handler_context.execute_step_args.get_command_args())
        )
        return iter(())

    def check_step_health(
        self, step_context: IStepContext, step_handler_context: StepHandlerContext
    ):
        return CheckStepHealthResult.healthy()

    def terminate_single_step(
        self, step_context: IStepContext, step_handler_context: StepHandlerContext
    ) -> Optional[Iterator[DagsterEvent]]:
        raise NotImplementedError()


def get_executor():
    return MultiEnvironmentExecutor(
        lambda _step_context: OutOfProcessSingleStepHandlerForTest(), retries=RetryMode.DISABLED
    )


def return_a_job():
    @op
    def return_one():
        return 1

    @job
    def a_job():
        return_one()

    defs = Definitions(jobs=[a_job], executor=get_executor())
    return defs.get_job_def("a_job")


def test_per_step_delegating_executor():
    ProcessCollection.reset()

    with instance_for_test() as instance:
        with execute_job(
            reconstructable(return_a_job),
            instance=instance,
        ) as result:
            ProcessCollection.wait_for_processes()

            assert result.success
            assert result.output_for_node("return_one") == 1

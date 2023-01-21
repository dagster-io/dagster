import subprocess
from contextlib import contextmanager
from typing import Callable, Iterator, Optional

from dagster import Definitions, job, op, reconstructable
from dagster._core.definitions.job_definition import JobDefinition
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
    def __init__(self):
        self.processes = []  # type: ignore

    def wait_for_processes(self):
        for p in self.processes:
            p.wait(timeout=5)


class SubprocessSingleStepHandler(RemoteEnvironmentSingleStepHandler):
    def __init__(self, process_collection: ProcessCollection):
        self.process_collection = process_collection

    def launch_single_step(
        self, step_context: IStepContext, step_handler_context: StepHandlerContext
    ) -> Optional[Iterator[DagsterEvent]]:
        self.process_collection.processes.append(
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


def get_subprocess_executor_with_monkey_patched_process_collection():
    collection = ProcessCollection()
    executor = MultiEnvironmentExecutor(
        lambda _step_context: SubprocessSingleStepHandler(collection),
        retries=RetryMode.DISABLED,
    )
    setattr(executor, "__collection", collection)
    return executor


@contextmanager
def execute_and_complete_job(job_fn: Callable):
    with instance_for_test() as instance:
        with execute_job(
            reconstructable(job_fn),
            instance=instance,
        ) as result:
            assert result.job_def.executor_def.executor_creation_fn
            executor = result.job_def.executor_def.executor_creation_fn(None)  # type: ignore
            collection = getattr(executor, "__collection")
            collection.wait_for_processes()
            yield result


def get_job_for_execution(job_def: JobDefinition):
    defs = Definitions(
        jobs=[job_def], executor=get_subprocess_executor_with_monkey_patched_process_collection()
    )
    return defs.get_job_def(job_def.name)


def return_single_op_job():
    @op
    def return_one():
        return 1

    @job
    def a_job():
        return_one()

    return get_job_for_execution(a_job)


def test_single_op_job():
    with execute_and_complete_job(return_single_op_job) as result:
        assert result.success
        assert result.output_for_node("return_one") == 1

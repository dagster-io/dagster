import subprocess
from contextlib import contextmanager
from typing import Callable, Iterator, Optional

from dagster import Definitions, job, op, reconstructable
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.events import DagsterEvent
from dagster._core.execution.api import execute_job
from dagster._core.execution.execute_job_result import ExecuteJobResult
from dagster._core.execution.retries import RetryMode
from dagster._core.executor.per_step.per_step_executor import (
    GenericRunExecutor,
    PluggableStepExecutorBasedRunExecutor,
    StepExecutor,
)
from dagster._core.executor.step_delegating import (
    CheckStepHealthResult,
)
from dagster._core.test_utils import instance_for_test


# This is what it would look like for a user to write a step executor
class SubprocessStepExecutor(StepExecutor):
    def execute(self) -> Optional[Iterator[DagsterEvent]]:
        self._popen = subprocess.Popen(
            self.step_handler_context.execute_step_args.get_command_args()
        )
        return None

    def check_step_health(self):
        return CheckStepHealthResult.healthy()

    def terminate(self) -> Optional[Iterator[DagsterEvent]]:
        raise NotImplementedError()

    def wait_for_completion(self):
        return self._popen.wait(timeout=5)


def get_executor(result: ExecuteJobResult) -> PluggableStepExecutorBasedRunExecutor:
    assert result.job_def.executor_def.executor_creation_fn
    return result.job_def.executor_def.executor_creation_fn(None)  # type: ignore


@contextmanager
def execute_and_complete_job(job_fn: Callable):
    with instance_for_test() as instance:
        with execute_job(
            reconstructable(job_fn),
            instance=instance,
        ) as result:
            executor = get_executor(result)
            for step_executor in executor.step_executors.values():
                assert isinstance(step_executor, SubprocessStepExecutor)
                step_executor.wait_for_completion()
            yield result, executor


def get_job_for_execution(job_def: JobDefinition):
    defs = Definitions(
        jobs=[job_def],
        executor=GenericRunExecutor(SubprocessStepExecutor, retries=RetryMode.DISABLED),
    )
    return defs.get_job_def(job_def.name)


def return_single_op_job():
    @op(tags={"step_executor": "subprocess"})
    def return_one():
        return 1

    @job
    def a_job():
        return_one()

    return get_job_for_execution(a_job)


def test_single_op_job():
    with execute_and_complete_job(return_single_op_job) as (result, executor):
        assert result.success
        assert result.output_for_node("return_one") == 1

        assert executor.step_count == 1
        assert isinstance(executor.step_executors["return_one"], SubprocessStepExecutor)


def return_multi_op_job():
    @op
    def return_one():
        return 1

    @op
    def return_two():
        return 2

    @op
    def add(x, y):
        return x + y

    @job
    def a_job():
        add(return_one(), return_two())

    return get_job_for_execution(a_job)


def test_multi_op_job():
    with execute_and_complete_job(return_multi_op_job) as (result, executor):
        assert result.success
        assert result.output_for_node("return_one") == 1
        assert result.output_for_node("return_two") == 2
        assert result.output_for_node("add") == 3

        assert executor.step_count == 3
        step_executors = executor.step_executors
        assert step_executors["return_one"].step_key == "return_one"
        assert step_executors["return_two"].step_key == "return_two"
        assert step_executors["add"].step_key == "add"

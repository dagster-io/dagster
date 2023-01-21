import subprocess
from contextlib import contextmanager
from typing import Callable, Dict, Iterator, Optional

from dagster import Definitions, job, op, reconstructable
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.events import DagsterEvent
from dagster._core.execution.api import execute_job
from dagster._core.execution.context.system import IStepContext
from dagster._core.execution.execute_job_result import ExecuteJobResult
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


class PerRunState:
    def __init__(self):
        self.processes = []  # type: ignore
        self.handler_dict: Dict[str, RemoteEnvironmentSingleStepHandler] = {}

    def wait_for_processes(self):
        for p in self.processes:
            p.wait(timeout=5)

    @property
    def step_count(self):
        return len(self.handler_dict)


class SubprocessSingleStepHandler(RemoteEnvironmentSingleStepHandler):
    def __init__(self, per_run_state: PerRunState):
        self.per_run_state = per_run_state

    def launch_single_step(
        self, step_context: IStepContext, step_handler_context: StepHandlerContext
    ) -> Optional[Iterator[DagsterEvent]]:
        self.per_run_state.processes.append(
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
    per_run_state = PerRunState()

    def _get_single_step_handler(step_context: IStepContext):
        step_handler = SubprocessSingleStepHandler(per_run_state)
        per_run_state.handler_dict[step_context.step.key] = step_handler
        return step_handler

    executor = MultiEnvironmentExecutor(
        single_step_handler_factory=_get_single_step_handler,
        retries=RetryMode.DISABLED,
    )
    setattr(executor, "__per_run_state_for_test", per_run_state)
    return executor


def get_per_run_state(result: ExecuteJobResult) -> PerRunState:
    assert result.job_def.executor_def.executor_creation_fn
    executor = result.job_def.executor_def.executor_creation_fn(None)  # type: ignore
    return getattr(executor, "__per_run_state_for_test")


@contextmanager
def execute_and_complete_job(job_fn: Callable):
    with instance_for_test() as instance:
        with execute_job(
            reconstructable(job_fn),
            instance=instance,
        ) as result:
            per_run_state = get_per_run_state(result)
            per_run_state.wait_for_processes()
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

        per_run_state = get_per_run_state(result)
        assert per_run_state.step_count == 1
        assert isinstance(per_run_state.handler_dict["return_one"], SubprocessSingleStepHandler)

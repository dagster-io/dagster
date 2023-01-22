import subprocess
from contextlib import contextmanager
from typing import Callable, Dict, Iterator, List, Optional

from dagster import Definitions, job, op, reconstructable
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.events import DagsterEvent
from dagster._core.execution.api import execute_job
from dagster._core.execution.context.system import IStepContext, StepExecutionContext
from dagster._core.execution.execute_job_result import ExecuteJobResult
from dagster._core.execution.retries import RetryMode
from dagster._core.executor.per_step.per_step_executor import (
    StepExecutor,
    StepExecutorBasedRunExecutor,
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
        self.processes: List[subprocess.Popen] = []
        self.handler_dict: Dict[str, SubprocessStepExecutor] = {}

    def wait_for_processes(self):
        for p in self.processes:
            p.wait(timeout=5)

    @property
    def step_count(self):
        return len(self.handler_dict)


class SubprocessStepExecutor(StepExecutor):
    def __init__(self, step_context: IStepContext, per_run_state: PerRunState):
        super().__init__(step_context)
        self.step_key = step_context.step.key
        self.per_run_state = per_run_state

    def execute(self, step_handler_context: StepHandlerContext) -> Optional[Iterator[DagsterEvent]]:
        self.per_run_state.processes.append(
            subprocess.Popen(step_handler_context.execute_step_args.get_command_args())
        )

    def check_step_health(self, step_handler_context: StepHandlerContext):
        return CheckStepHealthResult.healthy()

    def terminate(
        self, step_handler_context: StepHandlerContext
    ) -> Optional[Iterator[DagsterEvent]]:
        raise NotImplementedError()


def get_subprocess_executor_with_monkey_patched_process_collection():
    per_run_state = PerRunState()

    class SubprocessCurriedRunState(SubprocessStepExecutor):
        def __init__(self, step_context: IStepContext):
            super().__init__(step_context=step_context, per_run_state=per_run_state)

    step_executors = {"subprocess": SubprocessCurriedRunState}

    def _get_single_step_handler(step_context: IStepContext) -> SubprocessCurriedRunState:
        if "step_executor" in step_context.step.tags:
            step_executor_cls = step_executors[step_context.step.tags["step_executor"]]
            step_handler = step_executor_cls(step_context)
        else:
            step_handler = SubprocessCurriedRunState(
                step_context=step_context,
            )
        per_run_state.handler_dict[step_context.step.key] = step_handler
        return step_handler

    executor = StepExecutorBasedRunExecutor(
        step_executor_factory=_get_single_step_handler,
        retries=RetryMode.DISABLED,
    )
    setattr(executor, "__per_run_state_for_test", per_run_state)
    return executor


# def get_ergonomic_executor_construction():
#     # return RunWorkerExecutor[SubprocessStepExecutor](
#     #     retries=RetryMode.DISABLED
#     # )

#     executor = StepExecutorBasedExecutor[(
#         step_executor_factory=_get_single_step_handler,
#         retries=RetryMode.DISABLED,
#     )


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
    @op(tags={"step_executor": "subprocess"})
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
        assert isinstance(per_run_state.handler_dict["return_one"], SubprocessStepExecutor)


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
    with execute_and_complete_job(return_multi_op_job) as result:
        assert result.success
        assert result.output_for_node("return_one") == 1
        assert result.output_for_node("return_two") == 2
        assert result.output_for_node("add") == 3

        per_run_state = get_per_run_state(result)
        assert per_run_state.step_count == 3
        # we in fact get different object instances
        assert per_run_state.handler_dict["return_one"].step_key == "return_one"
        assert per_run_state.handler_dict["return_two"].step_key == "return_two"
        assert per_run_state.handler_dict["add"].step_key == "add"

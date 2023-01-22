from typing import Any, Callable, Dict, Iterator, List, Optional

from dagster import _check as check
from dagster._core.events import DagsterEvent
from dagster._core.execution.context.system import IStepContext, PlanOrchestrationContext
from dagster._core.execution.plan.plan import ExecutionPlan
from dagster._core.execution.retries import RetryMode
from dagster._core.executor.base import Executor
from dagster._core.executor.step_delegating.step_delegating_executor import StepDelegatingExecutor
from dagster._core.executor.step_delegating.step_handler.base import (
    CheckStepHealthResult,
    StepHandler,
    StepHandlerContext,
)


class StepHandlerForPerStepExecutor(StepHandler):
    def __init__(
        self,
        step_executor_factory: Callable[[IStepContext], "StepExecutor"],
    ):
        self._step_executor_factory = step_executor_factory

    @property
    def name(self) -> str:
        return "StepHandlerForPerStepExecutor"

    def handler_for_key(self, step_context: IStepContext) -> "StepExecutor":
        return self._step_executor_factory(step_context)

    def _get_step_context(self, step_handler_context: StepHandlerContext) -> IStepContext:
        step_keys = step_handler_context.step_keys
        check.invariant(len(step_keys) == 1)
        return step_handler_context.get_step_context(step_keys[0])

    def launch_step(self, step_handler_context: StepHandlerContext) -> Iterator[DagsterEvent]:
        step_context = self._get_step_context(step_handler_context)

        remote_handler = self.handler_for_key(step_context)

        yield DagsterEvent.step_worker_starting(
            step_context,
            message=f'Executing step "{step_context.step.key}" in external process',
            metadata_entries=[],
        )

        iterator = remote_handler.execute(step_handler_context)
        if iterator:
            yield from iterator

    def check_step_health(self, step_handler_context: StepHandlerContext) -> CheckStepHealthResult:
        step_context = self._get_step_context(step_handler_context)
        return self.handler_for_key(step_context).check_step_health(step_handler_context)

    def terminate_step(self, step_handler_context: StepHandlerContext) -> Iterator[DagsterEvent]:
        step_context = self._get_step_context(step_handler_context)
        iterator = self.handler_for_key(step_context).terminate(step_handler_context)
        if iterator:
            yield from iterator


class StepExecutor:
    def __init__(self, step_context: IStepContext):
        self.step_context = step_context

    def execute(self, step_handler_context: StepHandlerContext) -> Optional[Iterator[DagsterEvent]]:
        raise NotImplementedError()

    def terminate(
        self, step_handler_context: StepHandlerContext
    ) -> Optional[Iterator[DagsterEvent]]:
        raise NotImplementedError()

    def check_step_health(self, step_handler_context: StepHandlerContext):
        raise NotImplementedError()


class StepExecutorBasedRunExecutor(Executor):
    def __init__(
        self,
        step_executor_factory: Callable[[IStepContext], "StepExecutor"],
        retries: RetryMode,
        sleep_seconds: Optional[float] = None,
        check_step_health_interval_seconds: Optional[int] = None,
        max_concurrent: Optional[int] = None,
        tag_concurrency_limits: Optional[List[Dict[str, Any]]] = None,
        should_verify_step: bool = False,
    ):
        self._inner_executor = StepDelegatingExecutor(
            StepHandlerForPerStepExecutor(step_executor_factory),
            retries=retries,
            sleep_seconds=sleep_seconds,
            check_step_health_interval_seconds=check_step_health_interval_seconds,
            max_concurrent=max_concurrent,
            tag_concurrency_limits=tag_concurrency_limits,
            should_verify_step=should_verify_step,
        )

    def execute(self, plan_context: PlanOrchestrationContext, execution_plan: ExecutionPlan):
        return self._inner_executor.execute(plan_context, execution_plan)

    @property
    def retries(self) -> RetryMode:
        return self._inner_executor.retries

from typing import Callable, Iterator, Optional

from dagster import _check as check
from dagster._core.events import DagsterEvent
from dagster._core.execution.context.system import IStepContext, PlanOrchestrationContext
from dagster._core.execution.plan.plan import ExecutionPlan
from dagster._core.execution.retries import RetryMode
from dagster._core.executor.base import Executor
from dagster._core.executor.multi_environment.remote_step_information import (
    RemoteStepInformation,
    set_remote_step_info,
)
from dagster._core.executor.step_delegating.step_delegating_executor import StepDelegatingExecutor
from dagster._core.executor.step_delegating.step_handler.base import (
    CheckStepHealthResult,
    StepHandler,
    StepHandlerContext,
)


class MultiEnvironmentStepHandler(StepHandler):
    def __init__(
        self,
        single_step_handler_factory: Callable[[IStepContext], "RemoteEnvironmentSingleStepHandler"],
    ):
        self._single_step_handler_factory = single_step_handler_factory

    @property
    def name(self) -> str:
        return "MultiEnvironmentStepHandler"

    def handler_for_key(self, step_context: IStepContext) -> "RemoteEnvironmentSingleStepHandler":
        return self._single_step_handler_factory(step_context)

    def _get_step_context(self, step_handler_context: StepHandlerContext) -> IStepContext:
        step_keys = step_handler_context.step_keys
        check.invariant(len(step_keys) == 1)
        return step_handler_context.get_step_context(step_keys[0])

    def launch_step(self, step_handler_context: StepHandlerContext) -> Iterator[DagsterEvent]:
        step_context = self._get_step_context(step_handler_context)

        set_remote_step_info(
            instance=step_handler_context.instance,
            run_id=step_context.run_id,
            step_key=step_context.step.key,
            remote_step_info=RemoteStepInformation(
                retry_mode=step_handler_context.execute_step_args.retry_mode,
                known_state=step_handler_context.execute_step_args.known_state,
            ),
        )

        remote_handler = self.handler_for_key(step_context)
        # .launch_single_step(
        #     step_context, step_handler_context
        # )
        yield DagsterEvent.step_worker_starting(
            step_context,
            message=f'Executing step "{step_context.step.key}" in external process',
            metadata_entries=[],
        )

        iterator = remote_handler.launch_single_step(step_context, step_handler_context)
        if iterator:
            yield from iterator

    def check_step_health(self, step_handler_context: StepHandlerContext) -> CheckStepHealthResult:
        step_context = self._get_step_context(step_handler_context)
        return self.handler_for_key(step_context).check_step_health(
            step_context, step_handler_context
        )

    def terminate_step(self, step_handler_context: StepHandlerContext) -> Iterator[DagsterEvent]:
        step_context = self._get_step_context(step_handler_context)
        iterator = self.handler_for_key(step_context).terminate_single_step(
            step_context, step_handler_context
        )
        if iterator:
            yield from iterator


class RemoteEnvironmentSingleStepHandler:
    def launch_single_step(
        self, step_context: IStepContext, step_handler_context: StepHandlerContext
    ) -> Optional[Iterator[DagsterEvent]]:
        raise NotImplementedError()

    def terminate_single_step(
        self, step_context: IStepContext, step_handler_context: StepHandlerContext
    ) -> Optional[Iterator[DagsterEvent]]:
        raise NotImplementedError()

    def check_step_health(
        self, step_context: IStepContext, step_handler_context: StepHandlerContext
    ):
        raise NotImplementedError()


class MultiEnvironmentExecutor(Executor):
    def __init__(
        self,
        single_step_handler_factory: Callable[[IStepContext], "RemoteEnvironmentSingleStepHandler"],
        **kwargs,  # pass along all remaining executor args
    ):
        self._inner_executor = StepDelegatingExecutor(
            MultiEnvironmentStepHandler(single_step_handler_factory),
            **kwargs,
        )

    def execute(self, plan_context: PlanOrchestrationContext, execution_plan: ExecutionPlan):
        return self._inner_executor.execute(plan_context, execution_plan)

    @property
    def retries(self) -> RetryMode:
        return self._inner_executor.retries

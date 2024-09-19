from abc import ABC, abstractmethod
from typing import Iterator, Mapping, NamedTuple, Optional, Sequence

from dagster import (
    DagsterInstance,
    _check as check,
)
from dagster._core.events import DagsterEvent
from dagster._core.execution.context.system import IStepContext, PlanOrchestrationContext
from dagster._core.execution.plan.step import ExecutionStep
from dagster._core.storage.dagster_run import DagsterRun
from dagster._grpc.types import ExecuteStepArgs


class StepHandlerContext:
    def __init__(
        self,
        instance: DagsterInstance,
        plan_context: PlanOrchestrationContext,
        steps: Sequence[ExecutionStep],
        execute_step_args: ExecuteStepArgs,
        dagster_run: Optional[DagsterRun] = None,
    ) -> None:
        self._instance = instance
        self._plan_context = plan_context
        self._steps_by_key = {step.key: step for step in steps}
        self._execute_step_args = execute_step_args
        self._dagster_run = dagster_run

    @property
    def execute_step_args(self) -> ExecuteStepArgs:
        return self._execute_step_args

    @property
    def dagster_run(self) -> DagsterRun:
        # lazy load
        if not self._dagster_run:
            run_id = self.execute_step_args.run_id
            run = self._instance.get_run_by_id(run_id)
            if run is None:
                check.failed(f"Failed to load run {run_id}")
            self._dagster_run = run

        return self._dagster_run

    @property
    def step_tags(self) -> Mapping[str, Mapping[str, str]]:
        return {step_key: step.tags for step_key, step in self._steps_by_key.items()}

    @property
    def instance(self) -> DagsterInstance:
        return self._instance

    def get_step_context(self, step_key: str) -> IStepContext:
        return self._plan_context.for_step(self._steps_by_key[step_key])


class CheckStepHealthResult(
    NamedTuple(
        "_CheckStepHealthResult", [("is_healthy", bool), ("unhealthy_reason", Optional[str])]
    )
):
    def __new__(cls, is_healthy: bool, unhealthy_reason: Optional[str] = None):
        return super(CheckStepHealthResult, cls).__new__(
            cls,
            check.bool_param(is_healthy, "is_healthy"),
            check.opt_str_param(unhealthy_reason, "unhealthy_reason"),
        )

    @staticmethod
    def healthy() -> "CheckStepHealthResult":
        return CheckStepHealthResult(is_healthy=True)

    @staticmethod
    def unhealthy(reason: str) -> "CheckStepHealthResult":
        return CheckStepHealthResult(is_healthy=False, unhealthy_reason=reason)


class StepHandler(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def launch_step(self, step_handler_context: StepHandlerContext) -> Iterator[DagsterEvent]:
        pass

    @abstractmethod
    def check_step_health(self, step_handler_context: StepHandlerContext) -> CheckStepHealthResult:
        pass

    @abstractmethod
    def terminate_step(self, step_handler_context: StepHandlerContext) -> Iterator[DagsterEvent]:
        pass

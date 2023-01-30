from abc import ABC, abstractmethod
from typing import (
    Iterator,
    Optional,
)

from dagster import _check as check
from dagster._core.events import DagsterEvent
from dagster._core.execution.context.system import IStepContext
from dagster._core.executor.step_delegating.step_handler.base import (
    CheckStepHealthResult,
    StepHandlerContext,
)


class StepExecutor(ABC):
    def __init__(self, step_handler_context: StepHandlerContext, step_context: IStepContext):
        # Users will inherit from this so doing runtime checks
        self.step_handler_context = check.inst_param(
            step_handler_context, "step_handler_context", StepHandlerContext
        )
        self.step_context = check.inst_param(step_context, "step_context", IStepContext)

    @property
    def step_key(self) -> str:
        return self.step_context.step.key

    @abstractmethod
    def execute(self) -> Optional[Iterator[DagsterEvent]]:
        raise NotImplementedError()

    @abstractmethod
    def terminate(self) -> Optional[Iterator[DagsterEvent]]:
        raise NotImplementedError()

    @abstractmethod
    def check_step_health(self) -> CheckStepHealthResult:
        raise NotImplementedError()

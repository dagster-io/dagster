from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Iterator

from dagster._annotations import public
from dagster._core.execution.retries import RetryMode

if TYPE_CHECKING:
    from dagster._core.events import DagsterEvent
    from dagster._core.execution.context.system import PlanOrchestrationContext
    from dagster._core.execution.plan.plan import ExecutionPlan


class Executor(ABC):
    @public
    @abstractmethod
    def execute(
        self, plan_context: "PlanOrchestrationContext", execution_plan: "ExecutionPlan"
    ) -> Iterator["DagsterEvent"]:
        """For the given context and execution plan, orchestrate a series of sub plan executions in a way that satisfies the whole plan being executed.

        Args:
            plan_context (PlanOrchestrationContext): The plan's orchestration context.
            execution_plan (ExecutionPlan): The plan to execute.

        Returns:
            A stream of dagster events.
        """

    @public
    @property
    @abstractmethod
    def retries(self) -> RetryMode:
        """Whether retries are enabled or disabled for this instance of the executor.

        Executors should allow this to be controlled via configuration if possible.

        Returns: RetryMode
        """

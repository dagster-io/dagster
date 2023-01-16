from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Iterator

from dagster._annotations import public
from dagster._core.execution.retries import RetryMode

if TYPE_CHECKING:
    from dagster._core.events import DagsterEvent


class Executor(ABC):
    @public
    @abstractmethod
    def execute(self, plan_context, execution_plan) -> Iterator["DagsterEvent"]:
        """
        For the given context and execution plan, orchestrate a series of sub plan executions in a way that satisfies the whole plan being executed.

        Args:
            plan_context (PlanOrchestrationContext): The plan's orchestration context.
            execution_plan (ExecutionPlan): The plan to execute.

        Returns:
            A stream of dagster events.
        """

    @public  # type: ignore
    @property
    @abstractmethod
    def retries(self) -> RetryMode:
        """
        Whether retries are enabled or disabled for this instance of the executor.

        Executors should allow this to be controlled via configuration if possible.

        Returns: RetryMode
        """

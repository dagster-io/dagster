from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import TYPE_CHECKING

from dagster import _check as check
from dagster._annotations import public
from dagster._core.execution.plan.objects import StepFailureData, StepRetryData
from dagster._core.execution.retries import RetryMode
from dagster._utils.error import SerializableErrorInfo

if TYPE_CHECKING:
    from dagster._core.events import DagsterEvent
    from dagster._core.execution.context.system import IStepContext, PlanOrchestrationContext
    from dagster._core.execution.plan.plan import ExecutionPlan
    from dagster._core.execution.plan.state import KnownExecutionState


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

    def get_failure_or_retry_event_after_crash(
        self,
        step_context: "IStepContext",
        err_info: SerializableErrorInfo,
        known_state: "KnownExecutionState",
    ):
        from dagster._core.events import DagsterEvent

        # determine the retry policy for the step if needed
        retry_policy = step_context.op_retry_policy
        retry_state = known_state.get_retry_state()
        previous_attempt_count = retry_state.get_attempt_count(step_context.step.key)
        should_retry = (
            retry_policy
            and not step_context.retry_mode.disabled
            and previous_attempt_count < retry_policy.max_retries
        )

        if should_retry:
            return DagsterEvent.step_retry_event(
                step_context,
                StepRetryData(
                    error=err_info,
                    seconds_to_wait=check.not_none(retry_policy).calculate_delay(
                        previous_attempt_count + 1
                    ),
                ),
            )
        else:
            return DagsterEvent.step_failure_event(
                step_context=step_context,
                step_failure_data=StepFailureData(error=err_info, user_failure_data=None),
            )

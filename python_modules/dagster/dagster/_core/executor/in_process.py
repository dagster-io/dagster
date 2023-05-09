import os
from typing import Iterator, Optional

import dagster._check as check
from dagster._core.events import DagsterEvent, EngineEventData
from dagster._core.execution.api import ExecuteRunWithPlanIterable
from dagster._core.execution.context.system import PlanExecutionContext, PlanOrchestrationContext
from dagster._core.execution.context_creation_job import PlanExecutionContextManager
from dagster._core.execution.plan.execute_plan import inner_plan_execution_iterator
from dagster._core.execution.plan.plan import ExecutionPlan
from dagster._core.execution.retries import RetryMode
from dagster._utils.timing import format_duration, time_execution_scope

from .base import Executor


def in_process_plan_execution_iterator(
    job_context: PlanExecutionContext, execution_plan: ExecutionPlan
) -> Iterator[DagsterEvent]:
    # utility function that registers steps to iterate through, to enforce op concurrency.  This
    # explicit flag is required because the `inner_plan_execution_iterator` is also used to
    # coordinate the plan execution within the step workers, after the steps have already been
    # registered by the executor.
    return inner_plan_execution_iterator(job_context, execution_plan, register_steps=True)


class InProcessExecutor(Executor):
    def __init__(self, retries: RetryMode, marker_to_close: Optional[str] = None):
        self._retries = check.inst_param(retries, "retries", RetryMode)
        self.marker_to_close = check.opt_str_param(marker_to_close, "marker_to_close")

    @property
    def retries(self) -> RetryMode:
        return self._retries

    def execute(
        self, plan_context: PlanOrchestrationContext, execution_plan: ExecutionPlan
    ) -> Iterator[DagsterEvent]:
        check.inst_param(plan_context, "plan_context", PlanOrchestrationContext)
        check.inst_param(execution_plan, "execution_plan", ExecutionPlan)

        step_keys_to_execute = execution_plan.step_keys_to_execute

        yield DagsterEvent.engine_event(
            plan_context,
            f"Executing steps in process (pid: {os.getpid()})",
            event_specific_data=EngineEventData.in_process(os.getpid(), step_keys_to_execute),
        )

        with time_execution_scope() as timer_result:
            yield from iter(
                ExecuteRunWithPlanIterable(
                    execution_plan=plan_context.execution_plan,
                    iterator=in_process_plan_execution_iterator,
                    execution_context_manager=PlanExecutionContextManager(
                        job=plan_context.job,
                        retry_mode=plan_context.retry_mode,
                        execution_plan=plan_context.execution_plan,
                        run_config=plan_context.run_config,
                        dagster_run=plan_context.dagster_run,
                        instance=plan_context.instance,
                        raise_on_error=plan_context.raise_on_error,
                        output_capture=plan_context.output_capture,
                    ),
                )
            )

        yield DagsterEvent.engine_event(
            plan_context,
            "Finished steps in process (pid: {pid}) in {duration_ms}".format(
                pid=os.getpid(), duration_ms=format_duration(timer_result.millis)
            ),
            event_specific_data=EngineEventData.in_process(os.getpid(), step_keys_to_execute),
        )

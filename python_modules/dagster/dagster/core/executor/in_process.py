import os

from dagster import check
from dagster.core.events import DagsterEvent, EngineEventData
from dagster.core.execution.api import ExecuteRunWithPlanIterable
from dagster.core.execution.context.system import PlanOrchestrationContext
from dagster.core.execution.context_creation_pipeline import PlanExecutionContextManager
from dagster.core.execution.plan.execute_plan import inner_plan_execution_iterator
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.execution.retries import RetryMode
from dagster.utils.timing import format_duration, time_execution_scope

from .base import Executor


class InProcessExecutor(Executor):
    def __init__(self, retries, marker_to_close):
        self._retries = check.inst_param(retries, "retries", RetryMode)
        self.marker_to_close = check.opt_str_param(marker_to_close, "marker_to_close")

    @property
    def retries(self):
        return self._retries

    def execute(self, pipeline_context, execution_plan):
        check.inst_param(pipeline_context, "pipeline_context", PlanOrchestrationContext)
        check.inst_param(execution_plan, "execution_plan", ExecutionPlan)

        step_keys_to_execute = execution_plan.step_keys_to_execute

        yield DagsterEvent.engine_event(
            pipeline_context,
            "Executing steps in process (pid: {pid})".format(pid=os.getpid()),
            event_specific_data=EngineEventData.in_process(os.getpid(), step_keys_to_execute),
        )

        with time_execution_scope() as timer_result:
            yield from iter(
                ExecuteRunWithPlanIterable(
                    execution_plan=pipeline_context.execution_plan,
                    iterator=inner_plan_execution_iterator,
                    execution_context_manager=PlanExecutionContextManager(
                        pipeline=pipeline_context.pipeline,
                        retry_mode=pipeline_context.retry_mode,
                        execution_plan=pipeline_context.execution_plan,
                        run_config=pipeline_context.run_config,
                        pipeline_run=pipeline_context.pipeline_run,
                        instance=pipeline_context.instance,
                        raise_on_error=pipeline_context.raise_on_error,
                        output_capture=pipeline_context.output_capture,
                    ),
                )
            )

        yield DagsterEvent.engine_event(
            pipeline_context,
            "Finished steps in process (pid: {pid}) in {duration_ms}".format(
                pid=os.getpid(), duration_ms=format_duration(timer_result.millis)
            ),
            event_specific_data=EngineEventData.in_process(os.getpid(), step_keys_to_execute),
        )

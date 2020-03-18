import os

from dagster import check
from dagster.core.events import DagsterEvent, EngineEventData
from dagster.core.execution.config import ExecutorConfig
from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.execution.plan.execute import inner_plan_execution_iterator
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.utils.timing import format_duration, time_execution_scope

from .engine_base import Engine


class InProcessEngine(Engine):  # pylint: disable=no-init
    @staticmethod
    def execute(pipeline_context, execution_plan):
        check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
        check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)

        step_keys_to_execute = execution_plan.step_keys_to_execute

        yield DagsterEvent.engine_event(
            pipeline_context,
            'Executing steps in process (pid: {pid})'.format(pid=os.getpid()),
            event_specific_data=EngineEventData.in_process(os.getpid(), step_keys_to_execute,),
        )

        with time_execution_scope() as timer_result:
            check.param_invariant(
                isinstance(pipeline_context.executor_config, ExecutorConfig),
                'pipeline_context',
                'Expected executor_config to be ExecutorConfig got {}'.format(
                    pipeline_context.executor_config
                ),
            )

            for event in inner_plan_execution_iterator(
                pipeline_context, execution_plan, pipeline_context.executor_config.retries
            ):
                yield event

        yield DagsterEvent.engine_event(
            pipeline_context,
            'Finished steps in process (pid: {pid}) in {duration_ms}'.format(
                pid=os.getpid(), duration_ms=format_duration(timer_result.millis)
            ),
            event_specific_data=EngineEventData.in_process(os.getpid(), step_keys_to_execute),
        )

import os

from dagster import check

from dagster.core.execution_context import (
    MultiprocessExecutorConfig,
    SystemPipelineExecutionContext,
)
from dagster.core.events import DagsterEvent

from .create import create_execution_plan_core
from .objects import ExecutionPlan
from .simple_engine import start_inprocess_executor

from .child_process_executor import ChildProcessCommand, execute_child_process_command


class InProcessExecutorChildProcessCommand(ChildProcessCommand):
    def __init__(self, environment_dict, run_config, step_key):
        self.environment_dict = environment_dict
        self.run_config = run_config
        self.step_key = step_key

    def execute(self):
        from dagster.core.execution import yield_pipeline_execution_context

        check.inst(self.run_config.executor_config, MultiprocessExecutorConfig)
        pipeline = self.run_config.executor_config.pipeline_fn()

        with yield_pipeline_execution_context(
            pipeline, self.environment_dict, self.run_config.with_tags(pid=str(os.getpid()))
        ) as pipeline_context:

            execution_plan = create_execution_plan_core(
                pipeline_context.pipeline_def, pipeline_context.environment_config
            )

            for step_event in start_inprocess_executor(
                pipeline_context,
                execution_plan,
                pipeline_context.intermediates_manager,
                step_keys_to_execute=[self.step_key],
            ):
                yield step_event


def execute_step_out_of_process(step_context, step):
    check.invariant(
        not step_context.run_config.loggers,
        'Cannot inject loggers via RunConfig with the Multiprocess executor',
    )

    check.invariant(
        not step_context.event_callback, 'Cannot use event_callback across this process currently'
    )

    command = InProcessExecutorChildProcessCommand(
        step_context.environment_dict, step_context.run_config, step.key
    )

    for step_event in execute_child_process_command(command):
        yield step_event


def multiprocess_execute_plan(pipeline_context, execution_plan, step_keys_to_execute=None):
    check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
    check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
    check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)

    step_levels = execution_plan.topological_step_levels()

    intermediates_manager = pipeline_context.intermediates_manager

    step_key_set = None if step_keys_to_execute is None else set(step_keys_to_execute)

    # It would be good to implement a reference tracking algorithm here so we could
    # garbage collection results that are no longer needed by any steps
    # https://github.com/dagster-io/dagster/issues/811

    for step_level in step_levels:
        for step in step_level:
            if step_key_set and step.key not in step_key_set:
                continue

            step_context = pipeline_context.for_step(step)

            if not intermediates_manager.all_inputs_covered(step_context, step):
                expected_outputs = [ni.prev_output_handle for ni in step.step_inputs]

                step_context.log.error(
                    (
                        'Not all inputs covered for {step}. Not executing.'
                        'Outputs need for inputs {expected_outputs}'
                    ).format(expected_outputs=expected_outputs, step=step.key)
                )
                continue

            for step_event in check.generator(execute_step_out_of_process(step_context, step)):
                check.inst(step_event, DagsterEvent)
                yield step_event

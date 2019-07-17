import os
from dagster import check

from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.execution.config import MultiprocessExecutorConfig
from dagster.core.execution.plan.plan import ExecutionPlan

from .child_process_executor import ChildProcessCommand, execute_child_process_command
from .engine_base import IEngine
from .engine_inprocess import InProcessEngine


class InProcessExecutorChildProcessCommand(ChildProcessCommand):
    def __init__(self, environment_dict, run_config, step_key):
        self.environment_dict = environment_dict
        self.run_config = run_config
        self.step_key = step_key

    def execute(self):
        from dagster.core.execution.api import scoped_pipeline_context

        check.inst(self.run_config.executor_config, MultiprocessExecutorConfig)
        pipeline = self.run_config.executor_config.handle.build_pipeline_definition()

        with scoped_pipeline_context(
            pipeline, self.environment_dict, self.run_config.with_tags(pid=str(os.getpid()))
        ) as pipeline_context:

            execution_plan = ExecutionPlan.build(
                pipeline_context.pipeline_def,
                pipeline_context.environment_config,
                pipeline_context.mode_def,
            )

            for step_event in InProcessEngine.execute(
                pipeline_context, execution_plan, step_keys_to_execute=[self.step_key]
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


def bounded_parallel_executor(step_contexts, limit):
    pending_execution = list(step_contexts)
    active_iters = {}

    while pending_execution or active_iters:
        while len(active_iters) < limit and pending_execution:
            step_context = pending_execution.pop()
            step = step_context.step
            active_iters[step.key] = execute_step_out_of_process(step_context, step)

        empty_iters = []
        for key, step_iter in active_iters.items():
            try:
                event_or_none = next(step_iter)
                if event_or_none is None:
                    continue
                yield event_or_none
            except StopIteration:
                empty_iters.append(key)

        for key in empty_iters:
            del active_iters[key]


class MultiprocessEngine(IEngine):  # pylint: disable=no-init
    @staticmethod
    def execute(pipeline_context, execution_plan, step_keys_to_execute=None):
        check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
        check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)
        check.opt_list_param(step_keys_to_execute, 'step_keys_to_execute', of_type=str)

        step_levels = execution_plan.topological_step_levels()

        intermediates_manager = pipeline_context.intermediates_manager

        limit = pipeline_context.executor_config.max_concurrent

        step_key_set = None if step_keys_to_execute is None else set(step_keys_to_execute)

        # It would be good to implement a reference tracking algorithm here so we could
        # garbage collection results that are no longer needed by any steps
        # https://github.com/dagster-io/dagster/issues/811

        for step_level in step_levels:
            step_contexts_to_execute = []
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

                step_contexts_to_execute.append(step_context)

            for step_event in bounded_parallel_executor(step_contexts_to_execute, limit):
                yield step_event

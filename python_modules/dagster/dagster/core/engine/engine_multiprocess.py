import os

from dagster import check
from dagster.core.execution.api import create_execution_plan, execute_plan_iterator
from dagster.core.execution.config import MultiprocessExecutorConfig, RunConfig
from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.events import SqliteEventSink
from dagster.utils import safe_tempfile_path

from .child_process_executor import ChildProcessCommand, execute_child_process_command
from .engine_base import IEngine


class InProcessExecutorChildProcessCommand(ChildProcessCommand):
    def __init__(self, environment_dict, run_config, executor_config, step_key):
        self.environment_dict = environment_dict
        self.executor_config = executor_config
        self.run_config = run_config
        self.step_key = step_key

    def execute(self):
        check.inst(self.executor_config, MultiprocessExecutorConfig)
        pipeline_def = self.executor_config.handle.build_pipeline_definition()

        run_config = self.run_config.with_tags(pid=str(os.getpid()))

        environment_dict = dict(
            self.environment_dict,
            execution={
                'in_process': {'config': {'raise_on_error': self.executor_config.raise_on_error}}
            },
        )
        execution_plan = create_execution_plan(pipeline_def, environment_dict, run_config)

        for step_event in execute_plan_iterator(
            execution_plan, environment_dict, run_config, step_keys_to_execute=[self.step_key]
        ):
            yield step_event


def execute_step_out_of_process(step_context, step):

    with safe_tempfile_path() as sqlite_file:
        event_sink = SqliteEventSink(sqlite_file, raise_on_error=True)

        child_run_config = RunConfig(
            run_id=step_context.run_config.run_id,
            tags=step_context.run_config.tags,
            event_sink=event_sink,
            step_keys_to_execute=step_context.run_config.step_keys_to_execute,
            mode=step_context.run_config.mode,
        )

        command = InProcessExecutorChildProcessCommand(
            step_context.environment_dict, child_run_config, step_context.executor_config, step.key
        )

        with event_sink.log_forwarding(step_context.log):
            for event_or_none in execute_child_process_command(command):
                yield event_or_none


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
                    uncovered_inputs = intermediates_manager.uncovered_inputs(step_context, step)
                    step_context.log.error(
                        (
                            'Not all inputs covered for {step}. Not executing.'
                            'Output missing for inputs: {uncovered_inputs}'
                        ).format(uncovered_inputs=uncovered_inputs, step=step.key)
                    )
                    continue

                step_contexts_to_execute.append(step_context)

            for step_event in bounded_parallel_executor(step_contexts_to_execute, limit):
                yield step_event

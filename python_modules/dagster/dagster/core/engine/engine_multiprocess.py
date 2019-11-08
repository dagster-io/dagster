import os
import signal

from dagster import check
from dagster.core.errors import DagsterSubprocessError
from dagster.core.events import DagsterEvent, EngineEventData
from dagster.core.execution.api import create_execution_plan, execute_plan_iterator
from dagster.core.execution.config import MultiprocessExecutorConfig
from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.execution.memoization import copy_required_intermediates_for_execution
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.instance import DagsterInstance
from dagster.utils.timing import format_duration, time_execution_scope

from .child_process_executor import (
    ChildProcessCommand,
    ChildProcessDoneEvent,
    ChildProcessEvent,
    ChildProcessStartEvent,
    ChildProcessSystemErrorEvent,
    execute_child_process_command,
)
from .engine_base import Engine


class InProcessExecutorChildProcessCommand(ChildProcessCommand):
    def __init__(self, environment_dict, pipeline_run, executor_config, step_key, instance_ref):
        self.environment_dict = environment_dict
        self.executor_config = executor_config
        self.pipeline_run = pipeline_run
        self.step_key = step_key
        self.instance_ref = instance_ref

    def execute(self):
        check.inst(self.executor_config, MultiprocessExecutorConfig)
        pipeline_def = self.executor_config.handle.build_pipeline_definition()
        environment_dict = dict(self.environment_dict, execution={'in_process': {}})

        execution_plan = create_execution_plan(
            pipeline_def, environment_dict, self.pipeline_run
        ).build_subset_plan([self.step_key])

        for step_event in execute_plan_iterator(
            execution_plan,
            self.pipeline_run,
            environment_dict=environment_dict,
            instance=DagsterInstance.from_ref(self.instance_ref),
        ):
            yield step_event


def execute_step_out_of_process(step_context, step, pid_tracker):
    command = InProcessExecutorChildProcessCommand(
        step_context.environment_dict,
        step_context.pipeline_run,
        step_context.executor_config,
        step.key,
        step_context.instance.get_ref(),
    )

    for ret in execute_child_process_command(command):
        if ret is None or isinstance(ret, DagsterEvent):
            yield ret
        elif isinstance(ret, ChildProcessEvent):
            if isinstance(ret, ChildProcessStartEvent):
                pid_tracker[ret.pid] = None
            elif isinstance(ret, ChildProcessDoneEvent):
                del pid_tracker[ret.pid]
            elif isinstance(ret, ChildProcessSystemErrorEvent):
                pid_tracker[ret.pid] = ret.error_info
        # an interrupt occured during polling this process
        elif isinstance(ret, KeyboardInterrupt):
            # forward the interrupt to all known processes
            for pid in pid_tracker.keys():
                os.kill(pid, signal.SIGINT)
        else:
            check.failed('Unexpected return value from child process {}'.format(type(ret)))


def bounded_parallel_executor(step_contexts, limit):
    pending_execution = list(step_contexts)
    active_iters = {}
    pid_tracker = {}

    while pending_execution or active_iters:
        while len(active_iters) < limit and pending_execution:
            step_context = pending_execution.pop()
            step = step_context.step
            active_iters[step.key] = execute_step_out_of_process(step_context, step, pid_tracker)

        empty_iters = []
        for key, step_iter in active_iters.items():
            try:
                event_or_none = next(step_iter)
                if event_or_none is None:
                    continue
                else:
                    yield event_or_none

            except StopIteration:
                empty_iters.append(key)

        for key in empty_iters:
            del active_iters[key]

    errs = {pid: err for pid, err in pid_tracker.items() if err}
    if errs:
        raise DagsterSubprocessError(
            'During multiprocess execution errors occured in child processes:\n{error_list}'.format(
                error_list='\n'.join(
                    [
                        'In process {pid}: {err}'.format(pid=pid, err=err.to_string())
                        for pid, err in errs.items()
                    ]
                )
            ),
            subprocess_error_infos=list(errs.values()),
        )


class MultiprocessEngine(Engine):  # pylint: disable=no-init
    @staticmethod
    def execute(pipeline_context, execution_plan):
        check.inst_param(pipeline_context, 'pipeline_context', SystemPipelineExecutionContext)
        check.inst_param(execution_plan, 'execution_plan', ExecutionPlan)

        step_levels = execution_plan.execution_step_levels()

        intermediates_manager = pipeline_context.intermediates_manager

        limit = pipeline_context.executor_config.max_concurrent

        step_key_set = set(step.key for step in execution_plan.execution_steps())

        yield DagsterEvent.engine_event(
            pipeline_context,
            'Executing steps using multiprocess engine: parent process (pid: {pid})'.format(
                pid=os.getpid()
            ),
            event_specific_data=EngineEventData.multiprocess(
                os.getpid(), step_keys_to_execute=step_key_set
            ),
        )

        # It would be good to implement a reference tracking algorithm here so we could
        # garbage collection results that are no longer needed by any steps
        # https://github.com/dagster-io/dagster/issues/811
        with time_execution_scope() as timer_result:
            for event in copy_required_intermediates_for_execution(
                pipeline_context, execution_plan
            ):
                yield event

            for step_level in step_levels:
                step_contexts_to_execute = []
                for step in step_level:
                    step_context = pipeline_context.for_step(step)

                    if not intermediates_manager.all_inputs_covered(step_context, step):
                        uncovered_inputs = intermediates_manager.uncovered_inputs(
                            step_context, step
                        )
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

        yield DagsterEvent.engine_event(
            pipeline_context,
            'Multiprocess engine: parent process exiting after {duration} (pid: {pid})'.format(
                duration=format_duration(timer_result.millis), pid=os.getpid()
            ),
            event_specific_data=EngineEventData.multiprocess(os.getpid()),
        )

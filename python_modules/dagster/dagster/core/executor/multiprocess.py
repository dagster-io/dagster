import os
import sys

from dagster import EventMetadataEntry, check
from dagster.core.definitions.reconstructable import ReconstructablePipeline
from dagster.core.errors import DagsterExecutionInterruptedError, DagsterSubprocessError
from dagster.core.events import DagsterEvent, EngineEventData
from dagster.core.execution.api import create_execution_plan, execute_plan_iterator
from dagster.core.execution.context.system import SystemPipelineExecutionContext
from dagster.core.execution.plan.objects import StepFailureData
from dagster.core.execution.plan.plan import ExecutionPlan
from dagster.core.execution.retries import Retries
from dagster.core.executor.base import Executor
from dagster.core.instance import DagsterInstance
from dagster.seven import multiprocessing
from dagster.utils import start_termination_thread
from dagster.utils.error import serializable_error_info_from_exc_info
from dagster.utils.timing import format_duration, time_execution_scope

from .child_process_executor import (
    ChildProcessCommand,
    ChildProcessCrashException,
    ChildProcessEvent,
    ChildProcessSystemErrorEvent,
    execute_child_process_command,
)

DELEGATE_MARKER = "multiprocess_subprocess_init"


class InProcessExecutorChildProcessCommand(ChildProcessCommand):
    def __init__(
        self,
        run_config,
        pipeline_run,
        step_key,
        instance_ref,
        term_event,
        recon_pipeline,
        retries,
    ):
        self.run_config = run_config
        self.pipeline_run = pipeline_run
        self.step_key = step_key
        self.instance_ref = instance_ref
        self.term_event = term_event
        self.recon_pipeline = recon_pipeline
        self.retries = retries

    def execute(self):
        pipeline = self.recon_pipeline
        with DagsterInstance.from_ref(self.instance_ref) as instance:
            start_termination_thread(self.term_event)

            execution_plan = create_execution_plan(
                pipeline=pipeline,
                run_config=self.run_config,
                mode=self.pipeline_run.mode,
                step_keys_to_execute=self.pipeline_run.step_keys_to_execute,
            ).build_subset_plan([self.step_key])

            yield instance.report_engine_event(
                "Executing step {} in subprocess".format(self.step_key),
                self.pipeline_run,
                EngineEventData(
                    [
                        EventMetadataEntry.text(str(os.getpid()), "pid"),
                        EventMetadataEntry.text(self.step_key, "step_key"),
                    ],
                    marker_end=DELEGATE_MARKER,
                ),
                MultiprocessExecutor,
                self.step_key,
            )

            yield from execute_plan_iterator(
                execution_plan,
                self.pipeline_run,
                run_config=self.run_config,
                retries=self.retries.for_inner_plan(),
                instance=instance,
            )


class MultiprocessExecutor(Executor):
    def __init__(self, pipeline, retries, max_concurrent=None):

        self.pipeline = check.inst_param(pipeline, "pipeline", ReconstructablePipeline)
        self._retries = check.inst_param(retries, "retries", Retries)
        max_concurrent = max_concurrent if max_concurrent else multiprocessing.cpu_count()
        self.max_concurrent = check.int_param(max_concurrent, "max_concurrent")

    @property
    def retries(self):
        return self._retries

    def execute(self, pipeline_context, execution_plan):
        check.inst_param(pipeline_context, "pipeline_context", SystemPipelineExecutionContext)
        check.inst_param(execution_plan, "execution_plan", ExecutionPlan)

        limit = self.max_concurrent

        yield DagsterEvent.engine_event(
            pipeline_context,
            "Executing steps using multiprocess executor: parent process (pid: {pid})".format(
                pid=os.getpid()
            ),
            event_specific_data=EngineEventData.multiprocess(
                os.getpid(), step_keys_to_execute=execution_plan.step_keys_to_execute
            ),
        )

        # It would be good to implement a reference tracking algorithm here so we could
        # garbage collect results that are no longer needed by any steps
        # https://github.com/dagster-io/dagster/issues/811
        with time_execution_scope() as timer_result:
            with execution_plan.start(retries=self.retries) as active_execution:
                active_iters = {}
                errors = {}
                term_events = {}
                stopping = False

                while (not stopping and not active_execution.is_complete) or active_iters:
                    if active_execution.check_for_interrupts():
                        yield DagsterEvent.engine_event(
                            pipeline_context,
                            "Multiprocess executor: received termination signal - "
                            "forwarding to active child processes",
                            EngineEventData.interrupted(list(term_events.keys())),
                        )
                        stopping = True
                        active_execution.mark_interrupted()
                        for key, event in term_events.items():
                            event.set()

                    # start iterators
                    while len(active_iters) < limit and not stopping:
                        steps = active_execution.get_steps_to_execute(
                            limit=(limit - len(active_iters))
                        )

                        if not steps:
                            break

                        for step in steps:
                            step_context = pipeline_context.for_step(step)
                            term_events[step.key] = multiprocessing.Event()
                            active_iters[step.key] = self.execute_step_out_of_process(
                                step_context, step, errors, term_events
                            )

                    # process active iterators
                    empty_iters = []
                    for key, step_iter in active_iters.items():
                        try:
                            event_or_none = next(step_iter)
                            if event_or_none is None:
                                continue
                            else:
                                yield event_or_none
                                active_execution.handle_event(event_or_none)

                        except ChildProcessCrashException as crash:
                            serializable_error = serializable_error_info_from_exc_info(
                                sys.exc_info()
                            )
                            yield DagsterEvent.engine_event(
                                pipeline_context,
                                (
                                    "Multiprocess executor: child process for step {step_key} "
                                    "unexpectedly exited with code {exit_code}"
                                ).format(step_key=key, exit_code=crash.exit_code),
                                EngineEventData.engine_error(serializable_error),
                                step_handle=active_execution.get_step_by_key(key).handle,
                            )
                            step_failure_event = DagsterEvent.step_failure_event(
                                step_context=pipeline_context.for_step(
                                    active_execution.get_step_by_key(key)
                                ),
                                step_failure_data=StepFailureData(
                                    error=serializable_error, user_failure_data=None
                                ),
                            )
                            active_execution.handle_event(step_failure_event)
                            yield step_failure_event
                            empty_iters.append(key)
                        except StopIteration:
                            empty_iters.append(key)

                    # clear and mark complete finished iterators
                    for key in empty_iters:
                        del active_iters[key]
                        del term_events[key]
                        active_execution.verify_complete(pipeline_context, key)

                    # process skipped and abandoned steps
                    yield from active_execution.plan_events_iterator(pipeline_context)

                errs = {pid: err for pid, err in errors.items() if err}

                # After termination starts, raise an interrupted exception once all subprocesses
                # have finished cleaning up (and the only errors were from being interrupted)
                if (
                    stopping
                    and (not active_iters)
                    and all(
                        [
                            err_info.cls_name == "DagsterExecutionInterruptedError"
                            for err_info in errs.values()
                        ]
                    )
                ):
                    yield DagsterEvent.engine_event(
                        pipeline_context,
                        "Multiprocess executor: interrupted all active child processes",
                        event_specific_data=EngineEventData(),
                    )
                    raise DagsterExecutionInterruptedError()
                elif errs:
                    raise DagsterSubprocessError(
                        "During multiprocess execution errors occurred in child processes:\n{error_list}".format(
                            error_list="\n".join(
                                [
                                    "In process {pid}: {err}".format(pid=pid, err=err.to_string())
                                    for pid, err in errs.items()
                                ]
                            )
                        ),
                        subprocess_error_infos=list(errs.values()),
                    )

        yield DagsterEvent.engine_event(
            pipeline_context,
            "Multiprocess executor: parent process exiting after {duration} (pid: {pid})".format(
                duration=format_duration(timer_result.millis), pid=os.getpid()
            ),
            event_specific_data=EngineEventData.multiprocess(os.getpid()),
        )

    def execute_step_out_of_process(self, step_context, step, errors, term_events):
        command = InProcessExecutorChildProcessCommand(
            run_config=step_context.run_config,
            pipeline_run=step_context.pipeline_run,
            step_key=step.key,
            instance_ref=step_context.instance.get_ref(),
            term_event=term_events[step.key],
            recon_pipeline=self.pipeline,
            retries=self.retries,
        )

        yield DagsterEvent.engine_event(
            step_context,
            "Launching subprocess for {}".format(step.key),
            EngineEventData(marker_start=DELEGATE_MARKER),
            step_handle=step.handle,
        )

        for ret in execute_child_process_command(command):
            if ret is None or isinstance(ret, DagsterEvent):
                yield ret
            elif isinstance(ret, ChildProcessEvent):
                if isinstance(ret, ChildProcessSystemErrorEvent):
                    errors[ret.pid] = ret.error_info
            else:
                check.failed("Unexpected return value from child process {}".format(type(ret)))

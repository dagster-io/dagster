import multiprocessing
import os
import sys
from typing import List, Optional

from dagster import MetadataEntry
from dagster import _check as check
from dagster._core.errors import (
    DagsterExecutionInterruptedError,
    DagsterSubprocessError,
    DagsterUnmetExecutorRequirementsError,
)
from dagster._core.events import DagsterEvent, EngineEventData
from dagster._core.execution.api import create_execution_plan, execute_plan_iterator
from dagster._core.execution.context.system import PlanOrchestrationContext
from dagster._core.execution.context_creation_pipeline import create_context_free_log_manager
from dagster._core.execution.plan.objects import StepFailureData
from dagster._core.execution.plan.plan import ExecutionPlan
from dagster._core.execution.retries import RetryMode
from dagster._core.executor.base import Executor
from dagster._core.instance import DagsterInstance
from dagster._utils import start_termination_thread
from dagster._utils.error import serializable_error_info_from_exc_info
from dagster._utils.timing import format_duration, time_execution_scope

from .child_process_executor import (
    ChildProcessCommand,
    ChildProcessCrashException,
    ChildProcessEvent,
    ChildProcessSystemErrorEvent,
    execute_child_process_command,
)

DELEGATE_MARKER = "multiprocess_subprocess_init"


class MultiprocessExecutorChildProcessCommand(ChildProcessCommand):
    def __init__(
        self,
        run_config,
        pipeline_run,
        step_key,
        instance_ref,
        term_event,
        recon_pipeline,
        retry_mode,
        known_state,
        repository_load_data,
    ):
        self.run_config = run_config
        self.pipeline_run = pipeline_run
        self.step_key = step_key
        self.instance_ref = instance_ref
        self.term_event = term_event
        self.recon_pipeline = recon_pipeline
        self.retry_mode = retry_mode
        self.known_state = known_state
        self.repository_load_data = repository_load_data

    def execute(self):
        pipeline = self.recon_pipeline
        with DagsterInstance.from_ref(self.instance_ref) as instance:
            start_termination_thread(self.term_event)
            execution_plan = create_execution_plan(
                pipeline=pipeline,
                run_config=self.run_config,
                mode=self.pipeline_run.mode,
                step_keys_to_execute=[self.step_key],
                known_state=self.known_state,
                repository_load_data=self.repository_load_data,
            )

            log_manager = create_context_free_log_manager(instance, self.pipeline_run)

            yield DagsterEvent.step_worker_started(
                log_manager,
                self.pipeline_run.pipeline_name,
                message='Executing step "{}" in subprocess.'.format(self.step_key),
                metadata_entries=[
                    MetadataEntry("pid", value=str(os.getpid())),
                ],
                step_key=self.step_key,
            )

            yield from execute_plan_iterator(
                execution_plan,
                pipeline,
                self.pipeline_run,
                run_config=self.run_config,
                retry_mode=self.retry_mode.for_inner_plan(),
                instance=instance,
            )


class MultiprocessExecutor(Executor):
    def __init__(
        self,
        retries: RetryMode,
        max_concurrent: int,
        start_method: Optional[str] = None,
        explicit_forkserver_preload: Optional[List[str]] = None,
    ):
        self._retries = check.inst_param(retries, "retries", RetryMode)
        max_concurrent = max_concurrent if max_concurrent else multiprocessing.cpu_count()
        self._max_concurrent = check.int_param(max_concurrent, "max_concurrent")
        start_method = check.opt_str_param(start_method, "start_method")
        valid_starts = multiprocessing.get_all_start_methods()

        if start_method is None:
            start_method = "spawn"

        if start_method not in valid_starts:
            raise DagsterUnmetExecutorRequirementsError(
                f"The selected start_method '{start_method}' is not available. "
                f"Only {valid_starts} are valid options on {sys.platform} python {sys.version}.",
            )
        self._start_method = start_method
        self._explicit_forkserver_preload = explicit_forkserver_preload

    @property
    def retries(self):
        return self._retries

    def execute(self, plan_context, execution_plan):
        check.inst_param(plan_context, "plan_context", PlanOrchestrationContext)
        check.inst_param(execution_plan, "execution_plan", ExecutionPlan)

        pipeline = plan_context.reconstructable_pipeline

        multiproc_ctx = multiprocessing.get_context(self._start_method)
        if self._start_method == "forkserver":
            # if explicitly listed in config we will use that
            if self._explicit_forkserver_preload is not None:
                preload = self._explicit_forkserver_preload

            # or if the reconstructable pipeline has a module target, we will use that
            elif pipeline.get_module():
                preload = [pipeline.get_module()]

            # base case is to preload the dagster library
            else:
                preload = ["dagster"]

            # we import this module first to avoid user code like
            # pyspark.serializers._hijack_namedtuple from breaking us
            if "dagster._core.executor.multiprocess" not in preload:
                preload = ["dagster._core.executor.multiprocess"] + preload

            multiproc_ctx.set_forkserver_preload(preload)

        limit = self._max_concurrent

        yield DagsterEvent.engine_event(
            plan_context,
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
            with execution_plan.start(retry_mode=self.retries) as active_execution:
                active_iters = {}
                errors = {}
                term_events = {}
                stopping = False

                while (not stopping and not active_execution.is_complete) or active_iters:
                    if active_execution.check_for_interrupts():
                        yield DagsterEvent.engine_event(
                            plan_context,
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
                            step_context = plan_context.for_step(step)
                            term_events[step.key] = multiproc_ctx.Event()
                            active_iters[step.key] = execute_step_out_of_process(
                                multiproc_ctx,
                                pipeline,
                                step_context,
                                step,
                                errors,
                                term_events,
                                self.retries,
                                active_execution.get_known_state(),
                                execution_plan.repository_load_data,
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
                            step_context = plan_context.for_step(
                                active_execution.get_step_by_key(key)
                            )
                            yield DagsterEvent.engine_event(
                                step_context,
                                (
                                    "Multiprocess executor: child process for step {step_key} "
                                    "unexpectedly exited with code {exit_code}"
                                ).format(step_key=key, exit_code=crash.exit_code),
                                EngineEventData.engine_error(serializable_error),
                            )
                            step_failure_event = DagsterEvent.step_failure_event(
                                step_context=plan_context.for_step(
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
                        active_execution.verify_complete(plan_context, key)

                    # process skipped and abandoned steps
                    yield from active_execution.plan_events_iterator(plan_context)

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
                        plan_context,
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
            plan_context,
            "Multiprocess executor: parent process exiting after {duration} (pid: {pid})".format(
                duration=format_duration(timer_result.millis), pid=os.getpid()
            ),
            event_specific_data=EngineEventData.multiprocess(os.getpid()),
        )


def execute_step_out_of_process(
    multiproc_ctx,
    pipeline,
    step_context,
    step,
    errors,
    term_events,
    retries,
    known_state,
    repository_load_data,
):
    command = MultiprocessExecutorChildProcessCommand(
        run_config=step_context.run_config,
        pipeline_run=step_context.pipeline_run,
        step_key=step.key,
        instance_ref=step_context.instance.get_ref(),
        term_event=term_events[step.key],
        recon_pipeline=pipeline,
        retry_mode=retries,
        known_state=known_state,
        repository_load_data=repository_load_data,
    )

    yield DagsterEvent.step_worker_starting(
        step_context,
        'Launching subprocess for "{}".'.format(step.key),
        metadata_entries=[],
    )

    for ret in execute_child_process_command(multiproc_ctx, command):
        if ret is None or isinstance(ret, DagsterEvent):
            yield ret
        elif isinstance(ret, ChildProcessEvent):
            if isinstance(ret, ChildProcessSystemErrorEvent):
                errors[ret.pid] = ret.error_info
        else:
            check.failed("Unexpected return value from child process {}".format(type(ret)))

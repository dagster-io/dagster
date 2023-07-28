import multiprocessing
import os
import sys
from contextlib import ExitStack
from multiprocessing.context import BaseContext as MultiprocessingBaseContext
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Mapping, Optional, Sequence

from dagster import (
    _check as check,
)
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.definitions.reconstruct import ReconstructableJob
from dagster._core.definitions.repository_definition import RepositoryLoadData
from dagster._core.errors import (
    DagsterExecutionInterruptedError,
    DagsterSubprocessError,
    DagsterUnmetExecutorRequirementsError,
)
from dagster._core.events import DagsterEvent, EngineEventData
from dagster._core.execution.api import create_execution_plan, execute_plan_iterator
from dagster._core.execution.context.system import IStepContext, PlanOrchestrationContext
from dagster._core.execution.context_creation_job import create_context_free_log_manager
from dagster._core.execution.plan.active import ActiveExecution
from dagster._core.execution.plan.instance_concurrency_context import InstanceConcurrencyContext
from dagster._core.execution.plan.objects import StepFailureData
from dagster._core.execution.plan.plan import ExecutionPlan
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.execution.plan.step import ExecutionStep
from dagster._core.execution.retries import RetryMode
from dagster._core.executor.base import Executor
from dagster._core.instance import DagsterInstance
from dagster._utils import get_run_crash_explanation, start_termination_thread
from dagster._utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info
from dagster._utils.timing import TimerResult, format_duration, time_execution_scope

from .child_process_executor import (
    ChildProcessCommand,
    ChildProcessCrashException,
    ChildProcessEvent,
    ChildProcessSystemErrorEvent,
    execute_child_process_command,
)

if TYPE_CHECKING:
    from dagster._core.instance.ref import InstanceRef
    from dagster._core.storage.dagster_run import DagsterRun

DELEGATE_MARKER = "multiprocess_subprocess_init"


class MultiprocessExecutorChildProcessCommand(ChildProcessCommand):
    def __init__(
        self,
        run_config: Mapping[str, object],
        dagster_run: "DagsterRun",
        step_key: str,
        instance_ref: "InstanceRef",
        term_event: Any,
        recon_pipeline: ReconstructableJob,
        retry_mode: RetryMode,
        known_state: Optional[KnownExecutionState],
        repository_load_data: Optional[RepositoryLoadData],
    ):
        self.run_config = run_config
        self.dagster_run = dagster_run
        self.step_key = step_key
        self.instance_ref = instance_ref
        self.term_event = term_event
        self.recon_pipeline = recon_pipeline
        self.retry_mode = retry_mode
        self.known_state = known_state
        self.repository_load_data = repository_load_data

    def execute(self) -> Iterator[DagsterEvent]:
        recon_job = self.recon_pipeline
        with DagsterInstance.from_ref(self.instance_ref) as instance:
            start_termination_thread(self.term_event)
            execution_plan = create_execution_plan(
                job=recon_job,
                run_config=self.run_config,
                step_keys_to_execute=[self.step_key],
                known_state=self.known_state,
                repository_load_data=self.repository_load_data,
            )

            log_manager = create_context_free_log_manager(instance, self.dagster_run)

            yield DagsterEvent.step_worker_started(
                log_manager,
                self.dagster_run.job_name,
                message=f'Executing step "{self.step_key}" in subprocess.',
                metadata={
                    "pid": MetadataValue.text(str(os.getpid())),
                },
                step_key=self.step_key,
            )

            yield from execute_plan_iterator(
                execution_plan,
                recon_job,
                self.dagster_run,
                run_config=self.run_config,
                retry_mode=self.retry_mode.for_inner_plan(),
                instance=instance,
            )


class MultiprocessExecutor(Executor):
    def __init__(
        self,
        retries: RetryMode,
        max_concurrent: Optional[int],
        tag_concurrency_limits: Optional[List[Dict[str, Any]]] = None,
        start_method: Optional[str] = None,
        explicit_forkserver_preload: Optional[Sequence[str]] = None,
    ):
        self._retries = check.inst_param(retries, "retries", RetryMode)
        if not max_concurrent:
            env_var_default = os.getenv("DAGSTER_MULTIPROCESS_EXECUTOR_MAX_CONCURRENT")
            max_concurrent = (
                int(env_var_default) if env_var_default else multiprocessing.cpu_count()
            )

        self._max_concurrent = check.int_param(max_concurrent, "max_concurrent")
        self._tag_concurrency_limits = check.opt_list_param(
            tag_concurrency_limits, "tag_concurrency_limits"
        )
        start_method = check.opt_str_param(start_method, "start_method")
        valid_starts = multiprocessing.get_all_start_methods()

        if start_method is None:
            start_method = "spawn"

        if start_method not in valid_starts:
            raise DagsterUnmetExecutorRequirementsError(
                (
                    f"The selected start_method '{start_method}' is not available. "
                    f"Only {valid_starts} are valid options on {sys.platform} python {sys.version}."
                ),
            )
        self._start_method = start_method
        self._explicit_forkserver_preload = explicit_forkserver_preload

    @property
    def retries(self) -> RetryMode:
        return self._retries

    def execute(
        self, plan_context: PlanOrchestrationContext, execution_plan: ExecutionPlan
    ) -> Iterator[DagsterEvent]:
        check.inst_param(plan_context, "plan_context", PlanOrchestrationContext)
        check.inst_param(execution_plan, "execution_plan", ExecutionPlan)

        job = plan_context.reconstructable_job

        multiproc_ctx = multiprocessing.get_context(self._start_method)
        if self._start_method == "forkserver":
            module = job.get_module()
            # if explicitly listed in config we will use that
            if self._explicit_forkserver_preload is not None:
                preload = self._explicit_forkserver_preload

            # or if the reconstructable job has a module target, we will use that
            elif module is not None:
                preload = [module]

            # base case is to preload the dagster library
            else:
                preload = ["dagster"]

            # we import this module first to avoid user code like
            # pyspark.serializers._hijack_namedtuple from breaking us
            if "dagster._core.executor.multiprocess" not in preload:
                preload = ["dagster._core.executor.multiprocess", *preload]

            multiproc_ctx.set_forkserver_preload(list(preload))

        limit = self._max_concurrent
        tag_concurrency_limits = self._tag_concurrency_limits

        yield DagsterEvent.engine_event(
            plan_context,
            "Executing steps using multiprocess executor: parent process (pid: {pid})".format(
                pid=os.getpid()
            ),
            event_specific_data=EngineEventData.multiprocess(
                os.getpid(), step_keys_to_execute=execution_plan.step_keys_to_execute
            ),
        )

        timer_result: Optional[TimerResult] = None
        with ExitStack() as stack:
            timer_result = stack.enter_context(time_execution_scope())
            instance_concurrency_context = stack.enter_context(
                InstanceConcurrencyContext(plan_context.instance, plan_context.run_id)
            )
            active_execution = stack.enter_context(
                ActiveExecution(
                    execution_plan,
                    retry_mode=self.retries,
                    max_concurrent=limit,
                    tag_concurrency_limits=tag_concurrency_limits,
                    instance_concurrency_context=instance_concurrency_context,
                )
            )
            active_iters: Dict[str, Iterator[Optional[DagsterEvent]]] = {}
            errors: Dict[int, SerializableErrorInfo] = {}
            term_events: Dict[str, Any] = {}
            stopping: bool = False

            while (not stopping and not active_execution.is_complete) or active_iters:
                if active_execution.check_for_interrupts():
                    yield DagsterEvent.engine_event(
                        plan_context,
                        (
                            "Multiprocess executor: received termination signal - "
                            "forwarding to active child processes"
                        ),
                        EngineEventData.interrupted(list(term_events.keys())),
                    )
                    stopping = True
                    active_execution.mark_interrupted()
                    for key, event in term_events.items():
                        event.set()

                while not stopping:
                    steps = active_execution.get_steps_to_execute(
                        limit=(limit - len(active_iters)),
                    )

                    if not steps:
                        break

                    for step in steps:
                        step_context = plan_context.for_step(step)
                        term_events[step.key] = multiproc_ctx.Event()
                        active_iters[step.key] = execute_step_out_of_process(
                            multiproc_ctx,
                            job,
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
                        serializable_error = serializable_error_info_from_exc_info(sys.exc_info())
                        step_context = plan_context.for_step(active_execution.get_step_by_key(key))
                        yield DagsterEvent.engine_event(
                            step_context,
                            get_run_crash_explanation(
                                prefix=f"Multiprocess executor: child process for step {key}",
                                exit_code=crash.exit_code,
                            ),
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
                    "During multiprocess execution errors occurred in child"
                    " processes:\n{error_list}".format(
                        error_list="\n".join(
                            [f"In process {pid}: {err.to_string()}" for pid, err in errs.items()]
                        )
                    ),
                    subprocess_error_infos=list(errs.values()),
                )

        if timer_result:
            yield DagsterEvent.engine_event(
                plan_context,
                "Multiprocess executor: parent process exiting after {duration} (pid: {pid})"
                .format(duration=format_duration(timer_result.millis), pid=os.getpid()),
                event_specific_data=EngineEventData.multiprocess(os.getpid()),
            )


def execute_step_out_of_process(
    multiproc_ctx: MultiprocessingBaseContext,
    recon_job: ReconstructableJob,
    step_context: IStepContext,
    step: ExecutionStep,
    errors: Dict[int, SerializableErrorInfo],
    term_events: Dict[str, Any],
    retries: RetryMode,
    known_state: KnownExecutionState,
    repository_load_data: Optional[RepositoryLoadData],
) -> Iterator[Optional[DagsterEvent]]:
    command = MultiprocessExecutorChildProcessCommand(
        run_config=step_context.run_config,
        dagster_run=step_context.dagster_run,
        step_key=step.key,
        instance_ref=step_context.instance.get_ref(),
        term_event=term_events[step.key],
        recon_pipeline=recon_job,
        retry_mode=retries,
        known_state=known_state,
        repository_load_data=repository_load_data,
    )

    yield DagsterEvent.step_worker_starting(
        step_context,
        f'Launching subprocess for "{step.key}".',
        metadata={},
    )

    for ret in execute_child_process_command(multiproc_ctx, command):
        if ret is None or isinstance(ret, DagsterEvent):
            yield ret
        elif isinstance(ret, ChildProcessEvent):
            if isinstance(ret, ChildProcessSystemErrorEvent):
                errors[ret.pid] = ret.error_info
        else:
            check.failed(f"Unexpected return value from child process {type(ret)}")

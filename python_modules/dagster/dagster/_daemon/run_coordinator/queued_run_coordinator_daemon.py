import json
import sys
import threading
import time
from collections.abc import Iterable, Iterator, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import ExitStack
from typing import Optional

from dagster import (
    DagsterEvent,
    DagsterEventType,
    _check as check,
)
from dagster._core.errors import DagsterCodeLocationLoadError, DagsterUserCodeUnreachableError
from dagster._core.events import EngineEventData
from dagster._core.instance import DagsterInstance
from dagster._core.instance.config import ConcurrencyConfig
from dagster._core.launcher import LaunchRunContext
from dagster._core.op_concurrency_limits_counter import GlobalOpConcurrencyLimitsCounter
from dagster._core.run_coordinator.queued_run_coordinator import QueuedRunCoordinator
from dagster._core.storage.dagster_run import (
    IN_PROGRESS_RUN_STATUSES,
    DagsterRun,
    DagsterRunStatus,
    RunRecord,
    RunsFilter,
)
from dagster._core.storage.tags import PRIORITY_TAG
from dagster._core.utils import InheritContextThreadPoolExecutor
from dagster._core.workspace.context import BaseWorkspaceRequestContext, IWorkspaceProcessContext
from dagster._daemon.daemon import DaemonIterator, IntervalDaemon
from dagster._daemon.utils import DaemonErrorCapture
from dagster._utils.tags import TagConcurrencyLimitsCounter

PAGE_SIZE = 100


class QueuedRunCoordinatorDaemon(IntervalDaemon):
    """Used with the QueuedRunCoordinator on the instance. This process finds queued runs from the run
    store and launches them.
    """

    def __init__(self, interval_seconds, page_size=PAGE_SIZE) -> None:
        self._exit_stack = ExitStack()
        self._executor: Optional[ThreadPoolExecutor] = None
        self._location_timeouts_lock = threading.Lock()
        self._location_timeouts: dict[str, float] = {}
        self._page_size = page_size
        self._global_concurrency_blocked_runs_lock = threading.Lock()
        self._global_concurrency_blocked_runs = set()
        super().__init__(interval_seconds)

    def _get_executor(self, max_workers) -> ThreadPoolExecutor:
        if self._executor is None:
            # assumes max_workers wont change
            self._executor = self._exit_stack.enter_context(
                InheritContextThreadPoolExecutor(
                    max_workers=max_workers,
                    thread_name_prefix="run_dequeue_worker",
                )
            )
        return self._executor

    def __exit__(self, _exception_type, _exception_value, _traceback):
        self._executor = None
        self._exit_stack.close()
        super().__exit__(_exception_type, _exception_value, _traceback)

    @classmethod
    def daemon_type(cls) -> str:
        return "QUEUED_RUN_COORDINATOR"

    def run_iteration(
        self,
        workspace_process_context: IWorkspaceProcessContext,
        fixed_iteration_time: Optional[float] = None,  # used for tests
    ) -> DaemonIterator:
        if not isinstance(workspace_process_context.instance.run_coordinator, QueuedRunCoordinator):
            check.failed(
                f"Expected QueuedRunCoordinator, got {workspace_process_context.instance.run_coordinator}"
            )
        run_coordinator = check.inst(
            workspace_process_context.instance.run_coordinator, QueuedRunCoordinator
        )
        concurrency_config = workspace_process_context.instance.get_concurrency_config()
        if not concurrency_config.run_queue_config:
            check.failed("Got invalid run queue config")

        instance = workspace_process_context.instance
        runs_to_dequeue = self._get_runs_to_dequeue(
            instance, concurrency_config, fixed_iteration_time=fixed_iteration_time
        )
        yield from self._dequeue_runs_iter(
            workspace_process_context,
            run_coordinator,
            runs_to_dequeue,
            concurrency_config,
            fixed_iteration_time=fixed_iteration_time,
        )

    def _dequeue_runs_iter(
        self,
        workspace_process_context: IWorkspaceProcessContext,
        run_coordinator: QueuedRunCoordinator,
        runs_to_dequeue: list[DagsterRun],
        concurrency_config: ConcurrencyConfig,
        fixed_iteration_time: Optional[float],
    ) -> Iterator[None]:
        if run_coordinator.dequeue_use_threads:
            yield from self._dequeue_runs_iter_threaded(
                workspace_process_context,
                runs_to_dequeue,
                run_coordinator.dequeue_num_workers,
                concurrency_config,
                fixed_iteration_time=fixed_iteration_time,
            )
        else:
            yield from self._dequeue_runs_iter_loop(
                workspace_process_context,
                runs_to_dequeue,
                concurrency_config,
                fixed_iteration_time=fixed_iteration_time,
            )

    def _dequeue_run_thread(
        self,
        workspace_process_context: IWorkspaceProcessContext,
        run: DagsterRun,
        concurrency_config: ConcurrencyConfig,
        fixed_iteration_time: Optional[float],
    ) -> bool:
        return self._dequeue_run(
            workspace_process_context.instance,
            workspace_process_context.create_request_context(),
            run,
            concurrency_config,
            fixed_iteration_time,
        )

    def _dequeue_runs_iter_threaded(
        self,
        workspace_process_context: IWorkspaceProcessContext,
        runs_to_dequeue: list[DagsterRun],
        max_workers: Optional[int],
        concurrency_config: ConcurrencyConfig,
        fixed_iteration_time: Optional[float],
    ) -> Iterator[None]:
        num_dequeued_runs = 0

        for future in as_completed(
            self._get_executor(max_workers).submit(
                self._dequeue_run_thread,
                workspace_process_context,
                run,
                concurrency_config,
                fixed_iteration_time=fixed_iteration_time,
            )
            for run in runs_to_dequeue
        ):
            run_launched = future.result()
            yield None
            if run_launched:
                num_dequeued_runs += 1

        if num_dequeued_runs > 0:
            self._logger.info("Launched %d runs.", num_dequeued_runs)

    def _dequeue_runs_iter_loop(
        self,
        workspace_process_context: IWorkspaceProcessContext,
        runs_to_dequeue: list[DagsterRun],
        concurrency_config: ConcurrencyConfig,
        fixed_iteration_time: Optional[float],
    ) -> Iterator[None]:
        num_dequeued_runs = 0
        for run in runs_to_dequeue:
            run_launched = self._dequeue_run(
                workspace_process_context.instance,
                workspace_process_context.create_request_context(),
                run,
                concurrency_config,
                fixed_iteration_time=fixed_iteration_time,
            )
            yield None
            if run_launched:
                num_dequeued_runs += 1

        if num_dequeued_runs > 0:
            self._logger.info("Launched %d runs.", num_dequeued_runs)

    def _get_runs_to_dequeue(
        self,
        instance: DagsterInstance,
        concurrency_config: ConcurrencyConfig,
        fixed_iteration_time: Optional[float],
    ) -> list[DagsterRun]:
        if not isinstance(instance.run_coordinator, QueuedRunCoordinator):
            check.failed(f"Expected QueuedRunCoordinator, got {instance.run_coordinator}")

        run_queue_config = concurrency_config.run_queue_config
        assert run_queue_config
        max_concurrent_runs = run_queue_config.max_concurrent_runs
        tag_concurrency_limits = run_queue_config.tag_concurrency_limits

        in_progress_run_records = self._get_in_progress_run_records(instance)
        in_progress_runs = [record.dagster_run for record in in_progress_run_records]

        max_concurrent_runs_enabled = max_concurrent_runs != -1  # setting to -1 disables the limit
        max_runs_to_launch = max_concurrent_runs - len(in_progress_run_records)
        if max_concurrent_runs_enabled:
            # Possibly under 0 if runs were launched without queuing
            if max_runs_to_launch <= 0:
                self._logger.info(
                    f"{len(in_progress_run_records)} runs are currently in progress. Maximum is {max_concurrent_runs}, won't launch more."
                )
                return []

        cursor = None
        has_more = True
        batch: list[DagsterRun] = []

        now = fixed_iteration_time or time.time()

        with self._location_timeouts_lock:
            paused_location_names = {
                location_name
                for location_name in self._location_timeouts
                if self._location_timeouts[location_name] > now
            }

        locations_clause = ""
        if paused_location_names:
            locations_clause = (
                " Temporarily skipping runs from the following locations due to a user code error: "
                + ",".join(list(paused_location_names))
            )

        logged_this_iteration = False
        # Paginate through our runs list so we don't need to hold every run
        # in memory at once. The maximum number of runs we'll hold in memory is
        # max_runs_to_launch + page_size.
        while has_more:
            queued_runs = instance.get_runs(
                RunsFilter(statuses=[DagsterRunStatus.QUEUED]),
                cursor=cursor,
                limit=self._page_size,
                ascending=True,
            )
            has_more = len(queued_runs) >= self._page_size

            if not queued_runs:
                has_more = False
                return batch

            if not logged_this_iteration:
                logged_this_iteration = True
                self._logger.info(
                    "Priority sorting and checking tag concurrency limits for queued runs."
                    + locations_clause
                )

            cursor = queued_runs[-1].run_id

            tag_concurrency_limits_counter = TagConcurrencyLimitsCounter(
                tag_concurrency_limits, in_progress_runs
            )
            batch += queued_runs
            batch = self._priority_sort(batch)

            if run_queue_config.should_block_op_concurrency_limited_runs:
                try:
                    global_concurrency_limits_counter = GlobalOpConcurrencyLimitsCounter(
                        instance,
                        batch,
                        in_progress_run_records,
                        run_queue_config.op_concurrency_slot_buffer,
                        concurrency_config.pool_config.pool_granularity,
                    )
                except:
                    self._logger.exception("Failed to initialize op concurrency counter")
                    # when we cannot initialize the global concurrency counter, we should fall back
                    # to not blocking any runs based on op concurrency limits
                    global_concurrency_limits_counter = None
            else:
                global_concurrency_limits_counter = None

            to_remove = []
            for run in batch:
                if tag_concurrency_limits_counter.is_blocked(run):
                    to_remove.append(run)
                    continue
                else:
                    tag_concurrency_limits_counter.update_counters_with_launched_item(run)

                if (
                    global_concurrency_limits_counter
                    and global_concurrency_limits_counter.is_blocked(run)
                ):
                    to_remove.append(run)
                    if run.run_id not in self._global_concurrency_blocked_runs:
                        with self._global_concurrency_blocked_runs_lock:
                            self._global_concurrency_blocked_runs.add(run.run_id)
                        concurrency_blocked_info = json.dumps(
                            global_concurrency_limits_counter.get_blocked_run_debug_info(run)
                        )
                        self._logger.info(
                            f"Run {run.run_id} is blocked by global concurrency limits: {concurrency_blocked_info}"
                        )
                    continue
                elif global_concurrency_limits_counter:
                    global_concurrency_limits_counter.update_counters_with_launched_item(run)

                location_name = (
                    run.remote_job_origin.location_name if run.remote_job_origin else None
                )
                if location_name and location_name in paused_location_names:
                    to_remove.append(run)
                    continue

            for run in to_remove:
                batch.remove(run)

            if max_runs_to_launch >= 1:
                batch = batch[:max_runs_to_launch]

        return batch

    def _get_in_progress_run_records(self, instance: DagsterInstance) -> Sequence[RunRecord]:
        return instance.get_run_records(filters=RunsFilter(statuses=IN_PROGRESS_RUN_STATUSES))

    def _priority_sort(self, runs: Iterable[DagsterRun]) -> list[DagsterRun]:
        def get_priority(run: DagsterRun) -> int:
            priority_tag_value = run.tags.get(PRIORITY_TAG, "0")
            try:
                return int(priority_tag_value)
            except ValueError:
                return 0

        # sorted is stable, so fifo is maintained
        return sorted(runs, key=get_priority, reverse=True)

    def _is_location_pausing_dequeues(self, location_name: str, now: float) -> bool:
        with self._location_timeouts_lock:
            return (
                location_name in self._location_timeouts
                and self._location_timeouts[location_name] > now
            )

    def _dequeue_run(
        self,
        instance: DagsterInstance,
        workspace: BaseWorkspaceRequestContext,
        run: DagsterRun,
        concurrency_config: ConcurrencyConfig,
        fixed_iteration_time: Optional[float],
    ) -> bool:
        assert concurrency_config.run_queue_config
        # double check that the run is still queued before dequeing
        run = check.not_none(instance.get_run_by_id(run.run_id))
        with self._global_concurrency_blocked_runs_lock:
            if run.run_id in self._global_concurrency_blocked_runs:
                self._global_concurrency_blocked_runs.remove(run.run_id)

        now = fixed_iteration_time or time.time()

        if run.status != DagsterRunStatus.QUEUED:
            self._logger.info(
                "Run %s is now %s instead of QUEUED, skipping",
                run.run_id,
                run.status,
            )
            return False

        # Very old (pre 0.10.0) runs and programatically submitted runs may not have an
        # attached code location name
        location_name = run.remote_job_origin.location_name if run.remote_job_origin else None

        if location_name and self._is_location_pausing_dequeues(location_name, now):
            self._logger.info(
                "Pausing dequeues for runs from code location %s to give its code server time"
                " to recover",
                location_name,
            )
            return False

        launch_started_event = DagsterEvent(
            event_type_value=DagsterEventType.PIPELINE_STARTING.value,
            job_name=run.job_name,
        )

        instance.report_dagster_event(launch_started_event, run_id=run.run_id)

        run = check.not_none(instance.get_run_by_id(run.run_id))

        try:
            instance.run_launcher.launch_run(LaunchRunContext(dagster_run=run, workspace=workspace))
        except Exception as e:
            error = DaemonErrorCapture.process_exception(
                exc_info=sys.exc_info(),
                logger=self._logger,
                log_message=f"Caught on error dequeing run {run.run_id}",
            )

            run = check.not_none(instance.get_run_by_id(run.run_id))
            # Make sure we don't re-enqueue a run if it has already finished or moved into STARTED:
            if run.status not in (DagsterRunStatus.QUEUED, DagsterRunStatus.STARTING):
                self._logger.info(
                    f"Run {run.run_id} failed while being dequeued, but has already advanced to"
                    f" {run.status} - moving on. Error: {error.to_string()}"
                )
                return False
            elif concurrency_config.run_queue_config.max_user_code_failure_retries and isinstance(
                e, (DagsterUserCodeUnreachableError, DagsterCodeLocationLoadError)
            ):
                if location_name:
                    with self._location_timeouts_lock:
                        # Don't try to dequeue runs from this location for another N seconds
                        self._location_timeouts[location_name] = (
                            now + concurrency_config.run_queue_config.user_code_failure_retry_delay
                        )

                enqueue_event_records = instance.get_records_for_run(
                    run_id=run.run_id, of_type=DagsterEventType.PIPELINE_ENQUEUED
                ).records

                check.invariant(len(enqueue_event_records), "Could not find enqueue event for run")

                num_retries_so_far = len(enqueue_event_records) - 1

                if (
                    num_retries_so_far
                    >= concurrency_config.run_queue_config.max_user_code_failure_retries
                ):
                    message = (
                        "Run dequeue failed to reach the user code server after"
                        f" {concurrency_config.run_queue_config.max_user_code_failure_retries} attempts, failing run"
                    )
                    instance.report_engine_event(
                        message,
                        run,
                        EngineEventData.engine_error(error),
                    )
                    instance.report_run_failed(run)
                    return False
                else:
                    retries_left = (
                        concurrency_config.run_queue_config.max_user_code_failure_retries
                        - num_retries_so_far
                    )
                    retries_str = "retr" + ("y" if retries_left == 1 else "ies")
                    message = (
                        "Run dequeue failed to reach the user code server, re-submitting the run"
                        f" into the queue ({retries_left} {retries_str} remaining)"
                    )
                    instance.report_engine_event(
                        message,
                        run,
                        EngineEventData.engine_error(error),
                    )
                    # Re-submit the run into the queue
                    enqueued_event = DagsterEvent(
                        event_type_value=DagsterEventType.PIPELINE_ENQUEUED.value,
                        job_name=run.job_name,
                    )
                    instance.report_dagster_event(enqueued_event, run_id=run.run_id)
                    return False
            else:
                message = (
                    "Caught an unrecoverable error while dequeuing the run. Marking the run as"
                    " failed and dropping it from the queue"
                )

                instance.report_engine_event(
                    message,
                    run,
                    EngineEventData.engine_error(error),
                )

                instance.report_run_failed(run)
                return False
        return True

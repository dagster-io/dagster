import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import ExitStack
from typing import Dict, Iterable, Iterator, List, Optional, Sequence

from dagster import (
    DagsterEvent,
    DagsterEventType,
    _check as check,
)
from dagster._core.errors import (
    DagsterCodeLocationLoadError,
    DagsterUserCodeUnreachableError,
)
from dagster._core.events import EngineEventData
from dagster._core.instance import DagsterInstance
from dagster._core.launcher import LaunchRunContext
from dagster._core.run_coordinator.queued_run_coordinator import (
    QueuedRunCoordinator,
    RunQueueConfig,
)
from dagster._core.storage.dagster_run import (
    IN_PROGRESS_RUN_STATUSES,
    DagsterRun,
    DagsterRunStatus,
    RunsFilter,
)
from dagster._core.storage.tags import PRIORITY_TAG
from dagster._core.utils import InheritContextThreadPoolExecutor
from dagster._core.workspace.context import IWorkspaceProcessContext
from dagster._core.workspace.workspace import IWorkspace
from dagster._daemon.daemon import DaemonIterator, IntervalDaemon
from dagster._utils.error import serializable_error_info_from_exc_info
from dagster._utils.tags import TagConcurrencyLimitsCounter


class QueuedRunCoordinatorDaemon(IntervalDaemon):
    """Used with the QueuedRunCoordinator on the instance. This process finds queued runs from the run
    store and launches them.
    """

    def __init__(self, interval_seconds) -> None:
        self._exit_stack = ExitStack()
        self._executor: Optional[ThreadPoolExecutor] = None
        self._location_timeouts_lock = threading.Lock()
        self._location_timeouts: Dict[str, float] = {}
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
        run_coordinator = workspace_process_context.instance.run_coordinator
        if not isinstance(run_coordinator, QueuedRunCoordinator):
            check.failed(f"Expected QueuedRunCoordinator, got {run_coordinator}")

        run_queue_config = run_coordinator.get_run_queue_config()

        instance = workspace_process_context.instance
        runs_to_dequeue = self._get_runs_to_dequeue(
            instance, run_queue_config, fixed_iteration_time=fixed_iteration_time
        )
        yield from self._dequeue_runs_iter(
            workspace_process_context,
            run_coordinator,
            runs_to_dequeue,
            run_queue_config,
            fixed_iteration_time=fixed_iteration_time,
        )

    def _dequeue_runs_iter(
        self,
        workspace_process_context: IWorkspaceProcessContext,
        run_coordinator: QueuedRunCoordinator,
        runs_to_dequeue: List[DagsterRun],
        run_queue_config: RunQueueConfig,
        fixed_iteration_time: Optional[float],
    ) -> Iterator[None]:
        if run_coordinator.dequeue_use_threads:
            yield from self._dequeue_runs_iter_threaded(
                workspace_process_context,
                runs_to_dequeue,
                run_coordinator.dequeue_num_workers,
                run_queue_config,
                fixed_iteration_time=fixed_iteration_time,
            )
        else:
            yield from self._dequeue_runs_iter_loop(
                workspace_process_context,
                runs_to_dequeue,
                run_queue_config,
                fixed_iteration_time=fixed_iteration_time,
            )

    def _dequeue_run_thread(
        self,
        workspace_process_context: IWorkspaceProcessContext,
        run: DagsterRun,
        run_queue_config: RunQueueConfig,
        fixed_iteration_time: Optional[float],
    ) -> bool:
        return self._dequeue_run(
            workspace_process_context.instance,
            workspace_process_context.create_request_context(),
            run,
            run_queue_config,
            fixed_iteration_time,
        )

    def _dequeue_runs_iter_threaded(
        self,
        workspace_process_context: IWorkspaceProcessContext,
        runs_to_dequeue: List[DagsterRun],
        max_workers: Optional[int],
        run_queue_config: RunQueueConfig,
        fixed_iteration_time: Optional[float],
    ) -> Iterator[None]:
        num_dequeued_runs = 0

        for future in as_completed(
            self._get_executor(max_workers).submit(
                self._dequeue_run_thread,
                workspace_process_context,
                run,
                run_queue_config,
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
        runs_to_dequeue: List[DagsterRun],
        run_queue_config: RunQueueConfig,
        fixed_iteration_time: Optional[float],
    ) -> Iterator[None]:
        num_dequeued_runs = 0
        for run in runs_to_dequeue:
            run_launched = self._dequeue_run(
                workspace_process_context.instance,
                workspace_process_context.create_request_context(),
                run,
                run_queue_config,
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
        run_queue_config: RunQueueConfig,
        fixed_iteration_time: Optional[float],
    ) -> List[DagsterRun]:
        if not isinstance(instance.run_coordinator, QueuedRunCoordinator):
            check.failed(f"Expected QueuedRunCoordinator, got {instance.run_coordinator}")

        max_concurrent_runs = run_queue_config.max_concurrent_runs
        tag_concurrency_limits = run_queue_config.tag_concurrency_limits

        in_progress_runs = self._get_in_progress_runs(instance)

        max_concurrent_runs_enabled = max_concurrent_runs != -1  # setting to -1 disables the limit
        max_runs_to_launch = max_concurrent_runs - len(in_progress_runs)
        if max_concurrent_runs_enabled:
            # Possibly under 0 if runs were launched without queuing
            if max_runs_to_launch <= 0:
                self._logger.info(
                    "{} runs are currently in progress. Maximum is {}, won't launch more.".format(
                        len(in_progress_runs), max_concurrent_runs
                    )
                )
                return []

        queued_runs = self._get_queued_runs(instance)

        if not queued_runs:
            self._logger.debug("Poll returned no queued runs.")
            return []

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

        self._logger.info(
            f"Retrieved %d queued runs, checking limits.{locations_clause}",
            len(queued_runs),
        )

        # place in order
        sorted_runs = self._priority_sort(queued_runs)
        tag_concurrency_limits_counter = TagConcurrencyLimitsCounter(
            tag_concurrency_limits, in_progress_runs
        )

        batch: List[DagsterRun] = []
        for run in sorted_runs:
            if max_concurrent_runs_enabled and len(batch) >= max_runs_to_launch:
                break

            if tag_concurrency_limits_counter.is_blocked(run):
                continue

            location_name = (
                run.external_job_origin.location_name if run.external_job_origin else None
            )
            if location_name and location_name in paused_location_names:
                continue

            tag_concurrency_limits_counter.update_counters_with_launched_item(run)
            batch.append(run)

        return batch

    def _get_queued_runs(self, instance: DagsterInstance) -> Sequence[DagsterRun]:
        queued_runs_filter = RunsFilter(statuses=[DagsterRunStatus.QUEUED])

        # Reversed for fifo ordering
        runs = instance.get_runs(filters=queued_runs_filter)[::-1]
        return runs

    def _get_in_progress_runs(self, instance: DagsterInstance) -> Sequence[DagsterRun]:
        return instance.get_runs(filters=RunsFilter(statuses=IN_PROGRESS_RUN_STATUSES))

    def _priority_sort(self, runs: Iterable[DagsterRun]) -> Sequence[DagsterRun]:
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
        workspace: IWorkspace,
        run: DagsterRun,
        run_queue_config: RunQueueConfig,
        fixed_iteration_time: Optional[float],
    ) -> bool:
        # double check that the run is still queued before dequeing
        run = check.not_none(instance.get_run_by_id(run.run_id))

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
        location_name = run.external_job_origin.location_name if run.external_job_origin else None

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
            error = serializable_error_info_from_exc_info(sys.exc_info())

            run = check.not_none(instance.get_run_by_id(run.run_id))
            # Make sure we don't re-enqueue a run if it has already finished or moved into STARTED:
            if run.status not in (DagsterRunStatus.QUEUED, DagsterRunStatus.STARTING):
                self._logger.info(
                    f"Run {run.run_id} failed while being dequeued, but has already advanced to"
                    f" {run.status} - moving on. Error: {error.to_string()}"
                )
                return False
            elif run_queue_config.max_user_code_failure_retries and isinstance(
                e, (DagsterUserCodeUnreachableError, DagsterCodeLocationLoadError)
            ):
                if location_name:
                    with self._location_timeouts_lock:
                        # Don't try to dequeue runs from this location for another N seconds
                        self._location_timeouts[location_name] = (
                            now + run_queue_config.user_code_failure_retry_delay
                        )

                enqueue_event_records = instance.get_records_for_run(
                    run_id=run.run_id, of_type=DagsterEventType.PIPELINE_ENQUEUED
                ).records

                check.invariant(len(enqueue_event_records), "Could not find enqueue event for run")

                num_retries_so_far = len(enqueue_event_records) - 1

                if num_retries_so_far >= run_queue_config.max_user_code_failure_retries:
                    message = (
                        "Run dequeue failed to reach the user code server after"
                        f" {run_queue_config.max_user_code_failure_retries} attempts, failing run"
                    )
                    message_with_full_error = f"{message}: {error.to_string()}"
                    self._logger.error(message_with_full_error)
                    instance.report_engine_event(
                        message,
                        run,
                        EngineEventData.engine_error(error),
                    )
                    instance.report_run_failed(run)
                    return False
                else:
                    retries_left = (
                        run_queue_config.max_user_code_failure_retries - num_retries_so_far
                    )
                    retries_str = "retr" + ("y" if retries_left == 1 else "ies")
                    message = (
                        "Run dequeue failed to reach the user code server, re-submitting the run"
                        f" into the queue ({retries_left} {retries_str} remaining)"
                    )
                    message_with_full_error = f"{message}: {error.to_string()}"
                    self._logger.warning(message_with_full_error)

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
                message_with_full_error = f"{message}: {error.to_string()}"
                self._logger.error(message_with_full_error)

                instance.report_engine_event(
                    message,
                    run,
                    EngineEventData.engine_error(error),
                )

                instance.report_run_failed(run)
                return False
        return True

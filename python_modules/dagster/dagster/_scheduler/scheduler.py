import datetime
import logging
import os
import random
import sys
import threading
from collections import defaultdict
from collections.abc import Generator, Mapping, Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import AbstractContextManager, ExitStack
from typing import TYPE_CHECKING, Callable, NamedTuple, Optional, Union, cast

from typing_extensions import Self

import dagster._check as check
from dagster._core.definitions.schedule_definition import DefaultScheduleStatus
from dagster._core.definitions.timestamp import TimestampWithTimezone
from dagster._core.errors import (
    DagsterCodeLocationLoadError,
    DagsterInvariantViolationError,
    DagsterUserCodeUnreachableError,
)
from dagster._core.execution.submit_instigator_runs import (
    fetch_existing_runs_for_instigator,
    get_code_location_for_instigator,
    submit_instigator_run_request,
)
from dagster._core.instance import DagsterInstance
from dagster._core.remote_representation import RemoteSchedule
from dagster._core.scheduler.instigation import (
    InstigatorState,
    InstigatorStatus,
    InstigatorTick,
    InstigatorType,
    ScheduleInstigatorData,
    TickData,
    TickStatus,
)
from dagster._core.scheduler.scheduler import DEFAULT_MAX_CATCHUP_RUNS
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.storage.tags import SCHEDULED_EXECUTION_TIME_TAG
from dagster._core.utils import InheritContextThreadPoolExecutor, make_new_run_id
from dagster._core.workspace.context import IWorkspaceProcessContext
from dagster._daemon.utils import DaemonErrorCapture
from dagster._scheduler.stale import resolve_stale_or_missing_assets
from dagster._time import get_current_datetime, get_current_timestamp
from dagster._utils import DebugCrashFlags, SingleInstigatorDebugCrashFlags, check_for_debug_crash
from dagster._utils.error import SerializableErrorInfo
from dagster._utils.log import default_date_format_string
from dagster._utils.merger import merge_dicts

if TYPE_CHECKING:
    from dagster._daemon.daemon import DaemonIterator


# scheduler_id, next_iteration_timestamp, now
SchedulerDelayInstrumentation = Callable[[str, float, float], None]


def default_scheduler_delay_instrumentation(
    scheduler_id: str, next_iteration_timestamp: float, now_timestamp: float
) -> None:
    pass


# how often do we update the job row in the database with the last iteration timestamp.  This
# creates a checkpoint so that if the cron schedule changes, we don't try to backfill schedule ticks
# from the start of the schedule, just since the last recorded iteration interval.
LAST_ITERATION_CHECKPOINT_INTERVAL_SECONDS = int(
    os.getenv("DAGSTER_SCHEDULE_CHECKPOINT_INTERVAL_SECONDS", "3600")
)

LAST_ITERATION_CHECKPOINT_JITTER_SECONDS = int(
    os.getenv("DAGSTER_SCHEDULE_CHECKPOINT_JITTER_SECONDS", "600")
)

RETAIN_ORPHANED_STATE_INTERVAL_SECONDS = int(
    os.getenv("DAGSTER_SCHEDULE_ORPHANED_STATE_RETENTION_SECONDS", "43200")  # 12 hours
)

# How long to wait if an error is raised in the SchedulerDaemon iteration
ERROR_INTERVAL_TIME = 5


class _ScheduleLaunchContext(AbstractContextManager):
    def __init__(
        self,
        remote_schedule: RemoteSchedule,
        tick: InstigatorTick,
        instance: DagsterInstance,
        logger: logging.Logger,
        tick_retention_settings,
    ):
        self._remote_schedule = remote_schedule
        self._instance = instance
        self._logger = logger
        self._tick = tick
        self._purge_settings = defaultdict(set)
        for status, day_offset in tick_retention_settings.items():
            self._purge_settings[day_offset].add(status)

    @property
    def failure_count(self) -> int:
        return self._tick.tick_data.failure_count

    @property
    def consecutive_failure_count(self) -> int:
        return self._tick.tick_data.consecutive_failure_count or self._tick.tick_data.failure_count

    @property
    def tick_id(self) -> str:
        return str(self._tick.tick_id)

    @property
    def log_key(self) -> Sequence[str]:
        return [
            self._remote_schedule.handle.repository_name,
            self._remote_schedule.name,
            self.tick_id,
        ]

    def update_state(self, status, error=None, **kwargs):
        if status in {TickStatus.SKIPPED, TickStatus.SUCCESS}:
            kwargs["failure_count"] = 0
            kwargs["consecutive_failure_count"] = 0

        skip_reason = kwargs.get("skip_reason")
        kwargs.pop("skip_reason", None)

        self._tick = self._tick.with_status(status=status, error=error, **kwargs)

        if skip_reason:
            self._tick = self._tick.with_reason(skip_reason=skip_reason)

    def add_run_info(self, run_id=None, run_key=None):
        self._tick = self._tick.with_run_info(run_id, run_key)

    def add_log_key(self, log_key: Sequence[str]) -> None:
        self._tick = self._tick.with_log_key(log_key)

    def _write(self):
        self._instance.update_tick(self._tick)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self._write()
        for day_offset, statuses in self._purge_settings.items():
            if day_offset <= 0:
                continue
            self._instance.purge_ticks(
                self._remote_schedule.get_remote_origin_id(),
                selector_id=self._remote_schedule.selector_id,
                before=(get_current_datetime() - datetime.timedelta(days=day_offset)).timestamp(),
                tick_statuses=list(statuses),
            )


SECONDS_IN_MINUTE = 60


def _get_next_scheduler_iteration_time(start_time: float) -> float:
    # Wait until at least the next minute to run again, since the minimum granularity
    # for a cron schedule is every minute
    last_minute_time = start_time - (start_time % SECONDS_IN_MINUTE)
    return last_minute_time + SECONDS_IN_MINUTE


class ScheduleIterationTimes(NamedTuple):
    """Timestamp information returned by each scheduler iteration that the core scheduler
    loop can use to intelligently schedule the next tick.

    last_iteration_timestamp is used by subsequent evaluations of this schedule to ensure that we
    don't accidentally create incorrect runs after the cronstring changes (it is stored in memory
    in these objects and is also periodically persisted on the schedule row in the database -
    see _write_and_get_next_checkpoint_timestamp).

    next_iteration_timestamp is the timestamp until which the scheduler can wait until running this
    schedule again (assuming the cron schedule has not changed) - either because that's the next
    time we know the schedule needs to run based on the last time we evaluated its cron string,
    or because that's the next time we've determined that we should update the persisted
    last_iteration_timestamp value for this schedule described above (this is written on a fixed
    interval plus a random jitter value to ensure not every schedule tries to do this at once -
    this value is also determined in _write_and_get_next_checkpoint_timestamp.).
    """

    cron_schedule: Union[str, Sequence[str]]
    next_iteration_timestamp: float
    last_iteration_timestamp: float

    def should_run_next_iteration(self, schedule: RemoteSchedule, now_timestamp: float):
        if schedule.cron_schedule != self.cron_schedule:
            # cron schedule has changed - always run next iteration to check
            return True
        return now_timestamp >= self.next_iteration_timestamp


def execute_scheduler_iteration_loop(
    workspace_process_context: IWorkspaceProcessContext,
    logger: logging.Logger,
    max_catchup_runs: int,
    max_tick_retries: int,
    shutdown_event: threading.Event,
    scheduler_delay_instrumentation: SchedulerDelayInstrumentation = default_scheduler_delay_instrumentation,
) -> "DaemonIterator":
    from dagster._daemon.daemon import SpanMarker

    scheduler_run_futures: dict[str, Future] = {}
    iteration_times: dict[str, ScheduleIterationTimes] = {}

    threadpool_executor = None
    submit_threadpool_executor = None

    with ExitStack() as stack:
        settings = workspace_process_context.instance.get_scheduler_settings()
        if settings.get("use_threads"):
            threadpool_executor = stack.enter_context(
                InheritContextThreadPoolExecutor(
                    max_workers=settings.get("num_workers"),
                    thread_name_prefix="schedule_daemon_worker",
                )
            )
            num_submit_workers = settings.get("num_submit_workers")
            if num_submit_workers:
                submit_threadpool_executor = stack.enter_context(
                    InheritContextThreadPoolExecutor(
                        max_workers=settings.get("num_submit_workers"),
                        thread_name_prefix="schedule_submit_worker",
                    )
                )

        while True:
            start_time = get_current_timestamp()
            end_datetime_utc = get_current_datetime()

            next_interval_time = _get_next_scheduler_iteration_time(start_time)

            yield SpanMarker.START_SPAN

            try:
                yield from launch_scheduled_runs(
                    workspace_process_context,
                    logger,
                    end_datetime_utc=end_datetime_utc,
                    iteration_times=iteration_times,
                    threadpool_executor=threadpool_executor,
                    submit_threadpool_executor=submit_threadpool_executor,
                    scheduler_run_futures=scheduler_run_futures,
                    max_catchup_runs=max_catchup_runs,
                    max_tick_retries=max_tick_retries,
                    scheduler_delay_instrumentation=scheduler_delay_instrumentation,
                )
            except Exception:
                error_info = DaemonErrorCapture.process_exception(
                    exc_info=sys.exc_info(),
                    logger=logger,
                    log_message="SchedulerDaemon caught an error",
                )
                yield error_info
                # Wait a few seconds after an error
                next_interval_time = min(start_time + ERROR_INTERVAL_TIME, next_interval_time)

            yield SpanMarker.END_SPAN

            end_time = get_current_timestamp()
            if next_interval_time > end_time:
                # Sleep until the beginning of the next minute, plus a small epsilon to
                # be sure that we're past the start of the minute
                shutdown_event.wait(next_interval_time - end_time + 0.001)
                yield


def launch_scheduled_runs(
    workspace_process_context: IWorkspaceProcessContext,
    logger: logging.Logger,
    end_datetime_utc: datetime.datetime,
    iteration_times: dict[str, ScheduleIterationTimes],
    threadpool_executor: Optional[ThreadPoolExecutor] = None,
    submit_threadpool_executor: Optional[ThreadPoolExecutor] = None,
    scheduler_run_futures: Optional[dict[str, Future]] = None,
    max_catchup_runs: int = DEFAULT_MAX_CATCHUP_RUNS,
    max_tick_retries: int = 0,
    debug_crash_flags: Optional[DebugCrashFlags] = None,
    scheduler_delay_instrumentation: SchedulerDelayInstrumentation = default_scheduler_delay_instrumentation,
) -> "DaemonIterator":
    instance = workspace_process_context.instance

    current_workspace = {
        location_entry.origin.location_name: location_entry
        for location_entry in workspace_process_context.create_request_context()
        .get_code_location_entries()
        .values()
    }

    all_schedule_states = {
        schedule_state.selector_id: schedule_state
        for schedule_state in instance.all_instigator_state(instigator_type=InstigatorType.SCHEDULE)
    }

    tick_retention_settings = instance.get_tick_retention_settings(InstigatorType.SCHEDULE)

    running_schedules: dict[str, RemoteSchedule] = {}
    all_workspace_schedule_selector_ids = set()
    error_locations = set()

    now_timestamp = end_datetime_utc.timestamp()

    for location_entry in current_workspace.values():
        code_location = location_entry.code_location
        if code_location:
            for repo in code_location.get_repositories().values():
                for schedule in repo.get_schedules():
                    selector_id = schedule.selector_id
                    all_workspace_schedule_selector_ids.add(selector_id)
                    if schedule.get_current_instigator_state(
                        all_schedule_states.get(selector_id)
                    ).is_running:
                        running_schedules[selector_id] = schedule
                    elif all_schedule_states.get(selector_id):
                        schedule_state = all_schedule_states[selector_id]
                        # If there is a DB row to update, see if we should still update the
                        # last_iteration_timestamp
                        _write_and_get_next_checkpoint_timestamp(
                            instance,
                            all_schedule_states[selector_id],
                            cast("ScheduleInstigatorData", schedule_state.instigator_data),
                            now_timestamp,
                        )

        elif location_entry.load_error:
            error_locations.add(location_entry.origin.location_name)

    # Remove any schedule states that were previously created and can no longer
    # be found in the workspace (so that if they are later added back again,
    # their timestamps will start at the correct place)
    states_to_delete = [
        schedule_state
        for selector_id, schedule_state in all_schedule_states.items()
        if selector_id not in all_workspace_schedule_selector_ids
        or (
            schedule_state.status == InstigatorStatus.DECLARED_IN_CODE
            and not running_schedules.get(selector_id)
        )
    ]
    for state in states_to_delete:
        location_name = state.origin.repository_origin.code_location_origin.location_name

        if location_name in error_locations:
            # don't clean up state if its location is an error state
            continue

        _last_iteration_time = (
            state.instigator_data.last_iteration_timestamp or 0.0
            if isinstance(state.instigator_data, ScheduleInstigatorData)
            else 0.0
        )

        # Remove all-stopped states declared in code immediately.
        # Also remove all other states that are not present in the workspace after a 12-hour grace period.
        if state.status == InstigatorStatus.DECLARED_IN_CODE or (
            _last_iteration_time
            and _last_iteration_time + RETAIN_ORPHANED_STATE_INTERVAL_SECONDS
            < end_datetime_utc.timestamp()
        ):
            logger.info(
                f"Removing state for schedule {state.instigator_name} that is "
                f"no longer present in {location_name}."
            )
            instance.delete_instigator_state(state.instigator_origin_id, state.selector_id)

    if not running_schedules:
        yield
        return

    for schedule in running_schedules.values():
        error_info = None
        try:
            schedule_state = all_schedule_states.get(schedule.selector_id)
            if not schedule_state:
                assert schedule.default_status == DefaultScheduleStatus.RUNNING
                schedule_state = InstigatorState(
                    schedule.get_remote_origin(),
                    InstigatorType.SCHEDULE,
                    InstigatorStatus.DECLARED_IN_CODE,
                    ScheduleInstigatorData(
                        schedule.cron_schedule,
                        end_datetime_utc.timestamp(),
                    ),
                )
                instance.add_instigator_state(schedule_state)

            schedule_debug_crash_flags = (
                debug_crash_flags.get(schedule_state.instigator_name) if debug_crash_flags else None
            )

            if threadpool_executor:
                if scheduler_run_futures is None:
                    check.failed(
                        "scheduler_run_futures dict must be passed with threadpool_executor"
                    )

                if schedule.selector_id in scheduler_run_futures:
                    if scheduler_run_futures[schedule.selector_id].done():
                        try:
                            result = scheduler_run_futures[schedule.selector_id].result()
                            iteration_times[schedule.selector_id] = result
                        except Exception:
                            # Log exception and continue on rather than erroring the whole scheduler loop

                            DaemonErrorCapture.process_exception(
                                exc_info=sys.exc_info(),
                                logger=logger,
                                log_message=f"Error getting tick result for schedule {schedule.name}",
                            )
                        del scheduler_run_futures[schedule.selector_id]
                    else:
                        # only allow one tick per schedule to be in flight
                        continue

                previous_iteration_times = iteration_times.get(schedule.selector_id)
                if (
                    previous_iteration_times
                    and not previous_iteration_times.should_run_next_iteration(
                        schedule, end_datetime_utc.timestamp()
                    )
                ):
                    # Not enough time has passed for this schedule, don't bother creating a thread
                    continue

                if previous_iteration_times:
                    scheduler_delay_instrumentation(
                        schedule.selector_id,
                        previous_iteration_times.next_iteration_timestamp,
                        now_timestamp,
                    )

                future = threadpool_executor.submit(
                    launch_scheduled_runs_for_schedule,
                    workspace_process_context,
                    logger,
                    schedule,
                    schedule_state,
                    end_datetime_utc,
                    max_catchup_runs,
                    max_tick_retries,
                    tick_retention_settings,
                    schedule_debug_crash_flags,
                    submit_threadpool_executor=submit_threadpool_executor,
                    in_memory_last_iteration_timestamp=(
                        previous_iteration_times.last_iteration_timestamp
                        if previous_iteration_times
                        else None
                    ),
                )
                scheduler_run_futures[schedule.selector_id] = future
                yield

            else:
                previous_iteration_times = iteration_times.get(schedule.selector_id)
                if (
                    previous_iteration_times
                    and not previous_iteration_times.should_run_next_iteration(
                        schedule, end_datetime_utc.timestamp()
                    )
                ):
                    # Not enough time has passed for this schedule, don't bother executing
                    continue

                # evaluate the schedules in a loop, synchronously, yielding to allow the schedule daemon to
                # heartbeat
                found_iteration_times = False
                for yielded_value in launch_scheduled_runs_for_schedule_iterator(
                    workspace_process_context,
                    logger,
                    schedule,
                    schedule_state,
                    end_datetime_utc,
                    max_catchup_runs,
                    max_tick_retries,
                    tick_retention_settings,
                    schedule_debug_crash_flags,
                    submit_threadpool_executor=None,
                    in_memory_last_iteration_timestamp=(
                        previous_iteration_times.last_iteration_timestamp
                        if previous_iteration_times
                        else None
                    ),
                ):
                    if isinstance(yielded_value, ScheduleIterationTimes):
                        check.invariant(
                            not found_iteration_times,
                            "launch_scheduled_runs_for_schedule_iterator yielded more than one ScheduleIterationTimes",
                        )
                        found_iteration_times = True
                        iteration_times[schedule.selector_id] = yielded_value
                    else:
                        yield yielded_value
                check.invariant(
                    found_iteration_times,
                    "launch_scheduled_runs_for_schedule_iterator did not yield a ScheduleIterationTimes",
                )
        except Exception:
            error_info = DaemonErrorCapture.process_exception(
                exc_info=sys.exc_info(),
                logger=logger,
                log_message=f"Scheduler caught an error for schedule {schedule.name}",
            )

        yield error_info


def launch_scheduled_runs_for_schedule(
    workspace_process_context: IWorkspaceProcessContext,
    logger: logging.Logger,
    remote_schedule: RemoteSchedule,
    schedule_state: InstigatorState,
    end_datetime_utc: datetime.datetime,
    max_catchup_runs: int,
    max_tick_retries: int,
    tick_retention_settings: Mapping[TickStatus, int],
    schedule_debug_crash_flags: Optional[SingleInstigatorDebugCrashFlags],
    submit_threadpool_executor: Optional[ThreadPoolExecutor],
    in_memory_last_iteration_timestamp: Optional[float],
) -> ScheduleIterationTimes:
    # evaluate the tick immediately, but from within a thread.  The main thread should be able to
    # heartbeat to keep the daemon alive
    iteration_times = None
    for yielded_value in launch_scheduled_runs_for_schedule_iterator(
        workspace_process_context,
        logger,
        remote_schedule,
        schedule_state,
        end_datetime_utc,
        max_catchup_runs,
        max_tick_retries,
        tick_retention_settings,
        schedule_debug_crash_flags,
        submit_threadpool_executor=submit_threadpool_executor,
        in_memory_last_iteration_timestamp=in_memory_last_iteration_timestamp,
    ):
        if isinstance(yielded_value, ScheduleIterationTimes):
            iteration_times = yielded_value

    return check.not_none(iteration_times)


def launch_scheduled_runs_for_schedule_iterator(
    workspace_process_context: IWorkspaceProcessContext,
    logger: logging.Logger,
    remote_schedule: RemoteSchedule,
    schedule_state: InstigatorState,
    end_datetime_utc: datetime.datetime,
    max_catchup_runs: int,
    max_tick_retries: int,
    tick_retention_settings: Mapping[TickStatus, int],
    schedule_debug_crash_flags: Optional[SingleInstigatorDebugCrashFlags],
    submit_threadpool_executor: Optional[ThreadPoolExecutor],
    in_memory_last_iteration_timestamp: Optional[float],
) -> Generator[Union[None, SerializableErrorInfo, ScheduleIterationTimes], None, None]:
    schedule_state = check.inst_param(schedule_state, "schedule_state", InstigatorState)
    end_datetime_utc = check.inst_param(end_datetime_utc, "end_datetime_utc", datetime.datetime)
    instance = workspace_process_context.instance

    instigator_origin_id = remote_schedule.get_remote_origin_id()
    ticks = instance.get_ticks(instigator_origin_id, remote_schedule.selector_id, limit=1)
    latest_tick: Optional[InstigatorTick] = ticks[0] if ticks else None

    instigator_data = cast("ScheduleInstigatorData", schedule_state.instigator_data)
    start_timestamp_utc: float = instigator_data.start_timestamp or 0

    if latest_tick:
        if latest_tick.status == TickStatus.STARTED or (
            latest_tick.status == TickStatus.FAILURE
            and latest_tick.failure_count <= max_tick_retries
        ):
            # Scheduler was interrupted while performing this tick, re-do it
            start_timestamp_utc = max(
                start_timestamp_utc,
                latest_tick.timestamp,
                instigator_data.last_iteration_timestamp or 0.0,
                in_memory_last_iteration_timestamp or 0.0,
            )
        else:
            start_timestamp_utc = max(
                start_timestamp_utc,
                latest_tick.timestamp + 1,
                instigator_data.last_iteration_timestamp or 0.0,
                in_memory_last_iteration_timestamp or 0.0,
            )
    else:
        start_timestamp_utc = max(
            start_timestamp_utc,
            instigator_data.last_iteration_timestamp or 0.0,
            in_memory_last_iteration_timestamp or 0.0,
        )

    schedule_name = remote_schedule.name

    timezone_str = remote_schedule.execution_timezone
    if not timezone_str:
        timezone_str = "UTC"

    tick_times: list[datetime.datetime] = []

    now_timestamp = end_datetime_utc.timestamp()

    next_iteration_timestamp = None

    for next_time in remote_schedule.execution_time_iterator(start_timestamp_utc):
        next_tick_timestamp = next_time.timestamp()
        if next_tick_timestamp > now_timestamp:
            next_iteration_timestamp = next_tick_timestamp
            break

        tick_times.append(next_time)

    if not tick_times:
        next_checkpoint_timestamp = _write_and_get_next_checkpoint_timestamp(
            instance,
            schedule_state,
            instigator_data,
            now_timestamp,
        )

        next_iteration_timestamp = min(
            check.not_none(next_iteration_timestamp), next_checkpoint_timestamp
        )

        yield ScheduleIterationTimes(
            cron_schedule=remote_schedule.cron_schedule,
            next_iteration_timestamp=next_iteration_timestamp,
            last_iteration_timestamp=now_timestamp,
        )
        return

    if not remote_schedule.partition_set_name and len(tick_times) > 1:
        logger.warning(f"{schedule_name} has no partition set, so not trying to catch up")
        tick_times = tick_times[-1:]
    elif len(tick_times) > max_catchup_runs:
        logger.warning(f"{schedule_name} has fallen behind, only launching {max_catchup_runs} runs")
        tick_times = tick_times[-max_catchup_runs:]

    if len(tick_times) == 1:
        tick_time = tick_times[0].strftime(default_date_format_string())
        logger.info(f"Evaluating schedule `{schedule_name}` at {tick_time}")
    else:
        times = ", ".join([time.strftime(default_date_format_string()) for time in tick_times])
        logger.info(f"Evaluating schedule `{schedule_name}` at the following times: {times}")

    for schedule_time in tick_times:
        schedule_timestamp = schedule_time.timestamp()
        schedule_time_str = schedule_time.strftime(default_date_format_string())

        consecutive_failure_count = 0
        if latest_tick and latest_tick.status in {TickStatus.FAILURE, TickStatus.STARTED}:
            consecutive_failure_count = (
                latest_tick.consecutive_failure_count or latest_tick.failure_count
            )

        if latest_tick and latest_tick.timestamp == schedule_timestamp:
            tick = latest_tick
            if latest_tick.status == TickStatus.FAILURE:
                logger.info(f"Retrying previously failed schedule execution at {schedule_time_str}")
            else:
                logger.info(
                    f"Resuming previously interrupted schedule execution at {schedule_time_str}"
                )
        else:
            tick = instance.create_tick(
                TickData(
                    instigator_origin_id=instigator_origin_id,
                    instigator_name=schedule_name,
                    instigator_type=InstigatorType.SCHEDULE,
                    status=TickStatus.STARTED,
                    timestamp=schedule_timestamp,
                    selector_id=remote_schedule.selector_id,
                    consecutive_failure_count=consecutive_failure_count,
                )
            )

            check_for_debug_crash(schedule_debug_crash_flags, "TICK_CREATED")

        with _ScheduleLaunchContext(
            remote_schedule, tick, instance, logger, tick_retention_settings
        ) as tick_context:
            try:
                check_for_debug_crash(schedule_debug_crash_flags, "TICK_HELD")
                tick_context.add_log_key(tick_context.log_key)

                yield from _schedule_runs_at_time(
                    workspace_process_context,
                    logger,
                    remote_schedule,
                    schedule_time,
                    timezone_str,
                    tick_context,
                    submit_threadpool_executor,
                    schedule_debug_crash_flags,
                )
            except Exception as e:
                if isinstance(e, (DagsterUserCodeUnreachableError, DagsterCodeLocationLoadError)):
                    try:
                        raise DagsterUserCodeUnreachableError(
                            f"Unable to reach the user code server for schedule {schedule_name}."
                            " Schedule will resume execution once the server is available."
                        ) from e
                    except:
                        error_data = DaemonErrorCapture.process_exception(
                            sys.exc_info(),
                            logger=logger,
                            log_message=f"Scheduler daemon caught an error for schedule {remote_schedule.name}",
                        )
                        tick_context.update_state(
                            TickStatus.FAILURE,
                            error=error_data,
                            # don't increment the failure count - retry forever until the server comes back up
                            # or the schedule is turned off
                            failure_count=tick_context.failure_count,
                            consecutive_failure_count=tick_context.consecutive_failure_count + 1,
                        )
                        yield error_data
                else:
                    error_data = DaemonErrorCapture.process_exception(
                        sys.exc_info(),
                        logger=logger,
                        log_message=f"Scheduler daemon caught an error for schedule {remote_schedule.name}",
                    )
                    tick_context.update_state(
                        TickStatus.FAILURE,
                        error=error_data,
                        failure_count=tick_context.failure_count + 1,
                        consecutive_failure_count=tick_context.consecutive_failure_count + 1,
                    )
                    yield error_data

                # Plan to run the same tick again using the schedule timestamp
                # as both the next_iteration_timestamp and the last_iteration_timestmap
                # (to ensure that the scheduler doesn't accidentally skip past it)
                yield ScheduleIterationTimes(
                    cron_schedule=remote_schedule.cron_schedule,
                    next_iteration_timestamp=schedule_time.timestamp(),
                    last_iteration_timestamp=schedule_time.timestamp(),
                )
                return

    # now log the iteration timestamp
    next_checkpoint_timestamp = _write_and_get_next_checkpoint_timestamp(
        instance,
        schedule_state,
        instigator_data,
        end_datetime_utc.timestamp(),
    )
    next_iteration_timestamp = min(
        check.not_none(next_iteration_timestamp), next_checkpoint_timestamp
    )
    yield ScheduleIterationTimes(
        cron_schedule=remote_schedule.cron_schedule,
        next_iteration_timestamp=next_iteration_timestamp,
        last_iteration_timestamp=now_timestamp,
    )
    return


def _schedule_runs_at_time(
    workspace_process_context: IWorkspaceProcessContext,
    logger: logging.Logger,
    remote_schedule: RemoteSchedule,
    schedule_time: datetime.datetime,
    timezone_str: str,
    tick_context: _ScheduleLaunchContext,
    submit_threadpool_executor: Optional[ThreadPoolExecutor],
    debug_crash_flags: Optional[SingleInstigatorDebugCrashFlags] = None,
) -> Generator[Union[None, SerializableErrorInfo, ScheduleIterationTimes], None, None]:
    instance = workspace_process_context.instance
    repository_handle = remote_schedule.handle.repository_handle

    code_location = get_code_location_for_instigator(workspace_process_context, remote_schedule)

    schedule_execution_data = code_location.get_schedule_execution_data(
        instance=instance,
        repository_handle=repository_handle,
        schedule_name=remote_schedule.name,
        scheduled_execution_time=TimestampWithTimezone(
            schedule_time.timestamp(),
            timezone_str,
        ),
        log_key=tick_context.log_key,
    )
    yield None

    # Kept for backwards compatibility with schedule log keys that were previously created in the
    # schedule evaluation, rather than upfront.
    #
    # Note that to get schedule logs for failed schedule evaluations, we force users to update their
    # Dagster version.
    if schedule_execution_data.log_key:
        tick_context.add_log_key(schedule_execution_data.log_key)

    if not schedule_execution_data.run_requests:
        if schedule_execution_data.skip_message:
            logger.info(
                f"Schedule {remote_schedule.name} skipped: {schedule_execution_data.skip_message}"
            )
        else:
            logger.info(f"No run requests returned for {remote_schedule.name}, skipping")

        # Update tick to skipped state and return
        tick_context.update_state(
            TickStatus.SKIPPED, skip_reason=schedule_execution_data.skip_message
        )
        return

    run_requests = []

    for raw_run_request in schedule_execution_data.run_requests:
        run_request = raw_run_request.with_replaced_attrs(
            tags=merge_dicts(
                raw_run_request.tags,
                DagsterRun.tags_for_tick_id(tick_context.tick_id),
            )
        )

        if run_request.stale_assets_only:
            stale_assets = resolve_stale_or_missing_assets(
                workspace_process_context,  # type: ignore
                run_request,
                remote_schedule,
            )
            # asset selection is empty set after filtering for stale
            if len(stale_assets) == 0:
                continue
            else:
                run_request = run_request.with_replaced_attrs(
                    asset_selection=stale_assets, stale_assets_only=False
                )

        run_requests.append(run_request)

    additional_schedule_tags = {
        SCHEDULED_EXECUTION_TIME_TAG: schedule_time.astimezone(datetime.timezone.utc).isoformat(),
    }
    existing_runs = fetch_existing_runs_for_instigator(
        instance=instance,
        remote_instigator=remote_schedule,
        run_requests=run_requests,
        additional_tags=merge_dicts(
            DagsterRun.tags_for_schedule(remote_schedule),
            additional_schedule_tags,
        ),
    )
    submit_run_request = (
        lambda run_request: submit_instigator_run_request(
            run_id=make_new_run_id(),
            run_request=run_request,
            workspace_process_context=workspace_process_context,
            remote_instigator=remote_schedule,
            target_data=remote_schedule.get_target(),
            existing_runs_by_key=existing_runs,
            logger=logger,
            additional_tags=additional_schedule_tags,  # double check if  DagsterRun.tags_for_schedule(remote_schedule) needs to be added
            debug_crash_flags=debug_crash_flags,
        )
    )

    if submit_threadpool_executor:
        gen_run_request_results = submit_threadpool_executor.map(submit_run_request, run_requests)
    else:
        gen_run_request_results = map(submit_run_request, run_requests)

    for run_request_result in gen_run_request_results:
        yield run_request_result.error_info

        if not isinstance(run_request_result.run, DagsterRun):
            raise DagsterInvariantViolationError(
                f"RunRequestResults for a schedule should only return DagsterRuns. Got {type(run_request_result.run)}."
            )
        else:
            run = check.not_none(run_request_result.run)
            check_for_debug_crash(debug_crash_flags, "RUN_LAUNCHED")
            tick_context.add_run_info(run_id=run.run_id, run_key=run_request_result.run_key)
            check_for_debug_crash(debug_crash_flags, "RUN_ADDED")

    check_for_debug_crash(debug_crash_flags, "TICK_SUCCESS")
    tick_context.update_state(TickStatus.SUCCESS)


def _write_and_get_next_checkpoint_timestamp(
    instance: DagsterInstance,
    schedule_state: InstigatorState,
    instigator_data: ScheduleInstigatorData,
    iteration_timestamp: float,
) -> float:
    # Utility function that writes iteration timestamps for schedules, to record a
    # successful iteration, regardless of whether or not a tick was processed or not.  This is so
    # that when a cron schedule changes or a schedule changes state, we can modify the evaluation
    # "start time" from the moment that the schedule was turned on to the last time that the
    # schedule was processed in a valid state (even in between ticks).

    # Rather than logging every single iteration, we log every hour.  This means that if the cron
    # schedule changes to run to a time that is less than an hour ago, when the code location is
    # deployed, a tick might be registered for that time, with a run kicking off.

    # Returns the next timestamp that we should plan to log the last_iteration_timestamp - with some
    # additional jitter so that threads won't all come back at the exact same time
    random_jitter_offset = random.randint(0, LAST_ITERATION_CHECKPOINT_JITTER_SECONDS)

    if (
        not instigator_data.last_iteration_timestamp
        or instigator_data.last_iteration_timestamp + LAST_ITERATION_CHECKPOINT_INTERVAL_SECONDS
        <= iteration_timestamp
    ):
        instance.update_instigator_state(
            schedule_state.with_data(
                ScheduleInstigatorData(
                    cron_schedule=instigator_data.cron_schedule,
                    start_timestamp=instigator_data.start_timestamp,
                    last_iteration_timestamp=iteration_timestamp,
                )
            )
        )
        return (
            iteration_timestamp + LAST_ITERATION_CHECKPOINT_INTERVAL_SECONDS + random_jitter_offset
        )

    return (
        instigator_data.last_iteration_timestamp
        + LAST_ITERATION_CHECKPOINT_INTERVAL_SECONDS
        + random_jitter_offset
    )

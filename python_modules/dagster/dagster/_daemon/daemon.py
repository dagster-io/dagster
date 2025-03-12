import datetime
import logging
import os
import random
import sys
import time
import uuid
from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Generator, Mapping
from contextlib import AbstractContextManager, ExitStack
from enum import Enum
from threading import Event
from typing import Any, Generic, Optional, TypeVar, Union

from typing_extensions import TypeAlias

from dagster import (
    DagsterInstance,
    _check as check,
)
from dagster._core.remote_representation.external import RemoteSensor
from dagster._core.scheduler.scheduler import DagsterDaemonScheduler
from dagster._core.telemetry import DAEMON_ALIVE, log_action
from dagster._core.utils import InheritContextThreadPoolExecutor
from dagster._core.workspace.context import IWorkspaceProcessContext
from dagster._daemon.backfill import execute_backfill_iteration_loop
from dagster._daemon.monitoring import (
    execute_concurrency_slots_iteration,
    execute_run_monitoring_iteration,
)
from dagster._daemon.sensor import execute_sensor_iteration_loop
from dagster._daemon.types import DaemonHeartbeat
from dagster._daemon.utils import DaemonErrorCapture
from dagster._scheduler.scheduler import execute_scheduler_iteration_loop
from dagster._time import get_current_datetime
from dagster._utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info


def get_default_daemon_logger(daemon_name) -> logging.Logger:
    return logging.getLogger(f"dagster.daemon.{daemon_name}")


DAEMON_HEARTBEAT_ERROR_LIMIT = 5  # Show at most 5 errors
TELEMETRY_LOGGING_INTERVAL = 3600 * 24  # Interval (in seconds) at which to log that daemon is alive
_telemetry_daemon_session_id = str(uuid.uuid4())


def _get_error_sleep_interval():
    return int(os.getenv("DAGSTER_DAEMON_CORE_LOOP_EXCEPTION_SLEEP_INTERVAL", "5"))


def get_telemetry_daemon_session_id() -> str:
    return _telemetry_daemon_session_id


class SpanMarker(Enum):
    START_SPAN = "START_SPAN"
    END_SPAN = "END_SPAN"


DaemonIterator: TypeAlias = Generator[Union[None, SerializableErrorInfo, SpanMarker], None, None]

TContext = TypeVar("TContext", bound=IWorkspaceProcessContext)


class DagsterDaemon(AbstractContextManager, ABC, Generic[TContext]):
    _logger: logging.Logger
    _last_heartbeat_time: Optional[datetime.datetime]

    def __init__(self):
        self._logger = get_default_daemon_logger(type(self).__name__)

        self._last_heartbeat_time = None
        self._last_log_time = None
        self._errors = deque(
            maxlen=DAEMON_HEARTBEAT_ERROR_LIMIT
        )  # (SerializableErrorInfo, timestamp) tuples

        self._first_error_logged = False

    @classmethod
    @abstractmethod
    def daemon_type(cls) -> str:
        """returns: str."""

    def __exit__(self, _exception_type, _exception_value, _traceback):
        pass

    def run_daemon_loop(
        self,
        workspace_process_context: TContext,
        daemon_uuid: str,
        daemon_shutdown_event: Event,
        heartbeat_interval_seconds: float,
        error_interval_seconds: int,
    ):
        from dagster._core.telemetry_upload import uploading_logging_thread

        with uploading_logging_thread():
            daemon_generator = self.core_loop(workspace_process_context, daemon_shutdown_event)

            try:
                while not daemon_shutdown_event.is_set():
                    # Check to see if it's time to add a heartbeat initially and after each time
                    # the daemon yields
                    try:
                        self._check_add_heartbeat(
                            workspace_process_context.instance,
                            daemon_uuid,
                            heartbeat_interval_seconds,
                            error_interval_seconds,
                        )
                    except Exception:
                        self._logger.error(
                            "Failed to add heartbeat: \n%s",
                            serializable_error_info_from_exc_info(sys.exc_info()),
                        )

                    try:
                        result = next(daemon_generator)
                        if isinstance(result, SerializableErrorInfo):
                            self._errors.appendleft((result, get_current_datetime()))
                    except StopIteration:
                        self._logger.error(
                            "Daemon loop finished without raising an error - daemon loops should"
                            " run forever until they are interrupted."
                        )
                        break
                    except Exception:
                        error_info = DaemonErrorCapture.process_exception(
                            exc_info=sys.exc_info(),
                            logger=self._logger,
                            log_message="Caught error, daemon loop will restart",
                        )
                        self._errors.appendleft((error_info, get_current_datetime()))
                        daemon_generator.close()

                        # Wait a bit to ensure that errors don't happen in a tight loop
                        daemon_shutdown_event.wait(_get_error_sleep_interval())

                        daemon_generator = self.core_loop(
                            workspace_process_context, daemon_shutdown_event
                        )
            finally:
                # cleanup the generator if it was stopped part-way through
                daemon_generator.close()

    def _check_add_heartbeat(
        self,
        instance: DagsterInstance,
        daemon_uuid: str,
        heartbeat_interval_seconds: float,
        error_interval_seconds: int,
    ) -> None:
        error_max_time = get_current_datetime() - datetime.timedelta(seconds=error_interval_seconds)

        while len(self._errors):
            _earliest_error, earliest_timestamp = self._errors[-1]
            if earliest_timestamp >= error_max_time:
                break
            self._errors.pop()

        if instance.daemon_skip_heartbeats_without_errors and not self._errors:
            # no errors to report, so we don't write a heartbeat
            return

        curr_time = get_current_datetime()

        if (
            self._last_heartbeat_time
            and (curr_time - self._last_heartbeat_time).total_seconds() < heartbeat_interval_seconds
        ):
            return

        daemon_type = self.daemon_type()

        last_stored_heartbeat = instance.get_daemon_heartbeats().get(daemon_type)
        if (
            self._last_heartbeat_time
            and last_stored_heartbeat
            and last_stored_heartbeat.daemon_id != daemon_uuid
        ):
            self._logger.error(
                "Another %s daemon is still sending heartbeats. You likely have multiple "
                "daemon processes running at once, which is not supported. "
                "Last heartbeat daemon id: %s, "
                "Current daemon_id: %s",
                daemon_type,
                last_stored_heartbeat.daemon_id,
                daemon_uuid,
            )

        self._last_heartbeat_time = curr_time

        instance.add_daemon_heartbeat(
            DaemonHeartbeat(
                curr_time.timestamp(),
                daemon_type,
                daemon_uuid,
                errors=[error for (error, timestamp) in self._errors],
            )
        )
        if (
            not self._last_log_time
            or (curr_time - self._last_log_time).total_seconds() >= TELEMETRY_LOGGING_INTERVAL
        ):
            log_action(
                instance,
                DAEMON_ALIVE,
                metadata={"DAEMON_SESSION_ID": get_telemetry_daemon_session_id()},
            )
            self._last_log_time = curr_time

    @abstractmethod
    def core_loop(
        self,
        workspace_process_context: TContext,
        shutdown_event: Event,
    ) -> DaemonIterator:
        """Execute the daemon loop, which should be a generator function that never finishes.
        Should periodically yield so that the controller can check for heartbeats. Yields can be
        either NoneType or a SerializableErrorInfo.

        returns: generator (SerializableErrorInfo).
        """


class IntervalDaemon(DagsterDaemon[TContext], ABC):
    def __init__(
        self,
        interval_seconds,
        *,
        interval_jitter_seconds: float = 0,
        startup_jitter_seconds: float = 0,
    ):
        self.interval_seconds = check.numeric_param(interval_seconds, "interval_seconds")
        self.interval_jitter_seconds = interval_jitter_seconds
        self.startup_jitter_seconds = startup_jitter_seconds
        super().__init__()

    def core_loop(
        self,
        workspace_process_context: TContext,
        shutdown_event: Event,
    ) -> DaemonIterator:
        if self.startup_jitter_seconds:
            time.sleep(random.uniform(0, self.startup_jitter_seconds))

        while True:
            interval = self.interval_seconds + random.uniform(0, self.interval_jitter_seconds)
            start_time = time.time()
            yield SpanMarker.START_SPAN
            try:
                yield from self.run_iteration(workspace_process_context)
            except Exception:
                error_info = serializable_error_info_from_exc_info(sys.exc_info())
                self._logger.error("Caught error:\n%s", error_info)
                yield error_info
            yield SpanMarker.END_SPAN
            while time.time() - start_time < interval:
                shutdown_event.wait(0.5)
                yield None
            yield None

    @abstractmethod
    def run_iteration(self, workspace_process_context: TContext) -> DaemonIterator: ...


class SchedulerDaemon(DagsterDaemon):
    @classmethod
    def daemon_type(cls) -> str:
        return "SCHEDULER"

    def scheduler_delay_instrumentation(
        self, scheduler_id: str, next_iteration_timestamp: float, now_timestamp: float
    ) -> None:
        pass

    def core_loop(
        self,
        workspace_process_context: IWorkspaceProcessContext,
        shutdown_event: Event,
    ) -> DaemonIterator:
        scheduler = workspace_process_context.instance.scheduler
        if not isinstance(scheduler, DagsterDaemonScheduler):
            check.failed(f"Expected DagsterDaemonScheduler, got {scheduler}")

        yield from execute_scheduler_iteration_loop(
            workspace_process_context,
            self._logger,
            scheduler.max_catchup_runs,
            scheduler.max_tick_retries,
            shutdown_event,
            self.scheduler_delay_instrumentation,
        )


class SensorDaemon(DagsterDaemon):
    def __init__(self, settings: Mapping[str, Any]) -> None:
        super().__init__()
        self._exit_stack = ExitStack()
        self._threadpool_executor: Optional[InheritContextThreadPoolExecutor] = None
        self._submit_threadpool_executor: Optional[InheritContextThreadPoolExecutor] = None

        if settings.get("use_threads"):
            self._threadpool_executor = self._exit_stack.enter_context(
                InheritContextThreadPoolExecutor(
                    max_workers=settings.get("num_workers"),
                    thread_name_prefix="sensor_daemon_worker",
                )
            )
            num_submit_workers = settings.get("num_submit_workers")
            if num_submit_workers:
                self._submit_threadpool_executor = self._exit_stack.enter_context(
                    InheritContextThreadPoolExecutor(
                        max_workers=settings.get("num_submit_workers"),
                        thread_name_prefix="sensor_submit_worker",
                    )
                )

    def instrument_elapsed(
        self, sensor: RemoteSensor, elapsed: Optional[float], min_interval: int
    ) -> None:
        pass

    @classmethod
    def daemon_type(cls) -> str:
        return "SENSOR"

    def __exit__(self, _exception_type, _exception_value, _traceback):
        self._exit_stack.close()
        super().__exit__(_exception_type, _exception_value, _traceback)

    def core_loop(
        self,
        workspace_process_context: IWorkspaceProcessContext,
        shutdown_event: Event,
    ) -> DaemonIterator:
        yield from execute_sensor_iteration_loop(
            workspace_process_context,
            self._logger,
            shutdown_event,
            threadpool_executor=self._threadpool_executor,
            submit_threadpool_executor=self._submit_threadpool_executor,
            instrument_elapsed=self.instrument_elapsed,
        )


class BackfillDaemon(DagsterDaemon):
    def __init__(self, settings: Mapping[str, Any]) -> None:
        super().__init__()
        self._exit_stack = ExitStack()
        self._threadpool_executor: Optional[InheritContextThreadPoolExecutor] = None

        if settings.get("use_threads"):
            self._threadpool_executor = self._exit_stack.enter_context(
                InheritContextThreadPoolExecutor(
                    max_workers=settings.get("num_workers"),
                    thread_name_prefix="backfill_daemon_worker",
                )
            )

    @classmethod
    def daemon_type(cls) -> str:
        return "BACKFILL"

    def __exit__(self, _exception_type, _exception_value, _traceback):
        self._exit_stack.close()
        super().__exit__(_exception_type, _exception_value, _traceback)

    def core_loop(
        self,
        workspace_process_context: IWorkspaceProcessContext,
        shutdown_event: Event,
    ) -> DaemonIterator:
        yield from execute_backfill_iteration_loop(
            workspace_process_context,
            self._logger,
            shutdown_event,
            threadpool_executor=self._threadpool_executor,
        )


class MonitoringDaemon(IntervalDaemon):
    @classmethod
    def daemon_type(cls) -> str:
        return "MONITORING"

    def run_iteration(
        self,
        workspace_process_context: IWorkspaceProcessContext,
    ) -> DaemonIterator:
        yield from execute_run_monitoring_iteration(workspace_process_context, self._logger)
        yield from execute_concurrency_slots_iteration(workspace_process_context, self._logger)

import logging
import sys
import time
import uuid
from abc import ABC, abstractmethod
from collections import deque
from contextlib import AbstractContextManager
from threading import Event
from typing import Generator, Generic, TypeVar, Union

import pendulum

from dagster import (
    DagsterInstance,
    _check as check,
)
from dagster._core.scheduler.scheduler import DagsterDaemonScheduler
from dagster._core.telemetry import DAEMON_ALIVE, log_action
from dagster._core.workspace.context import IWorkspaceProcessContext
from dagster._daemon.backfill import execute_backfill_iteration
from dagster._daemon.monitoring import execute_monitoring_iteration
from dagster._daemon.sensor import execute_sensor_iteration_loop
from dagster._daemon.types import DaemonHeartbeat
from dagster._scheduler.scheduler import execute_scheduler_iteration_loop
from dagster._utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info


def get_default_daemon_logger(daemon_name) -> logging.Logger:
    return logging.getLogger(f"dagster.daemon.{daemon_name}")


DAEMON_HEARTBEAT_ERROR_LIMIT = 5  # Show at most 5 errors
TELEMETRY_LOGGING_INTERVAL = 3600 * 24  # Interval (in seconds) at which to log that daemon is alive
_telemetry_daemon_session_id = str(uuid.uuid4())


def get_telemetry_daemon_session_id() -> str:
    return _telemetry_daemon_session_id


TDaemonGenerator = Generator[Union[None, SerializableErrorInfo], None, None]

TContext = TypeVar("TContext", bound=IWorkspaceProcessContext)


class DagsterDaemon(AbstractContextManager, ABC, Generic[TContext]):
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
        """
        returns: str.
        """

    def __exit__(self, _exception_type, _exception_value, _traceback):
        pass

    def run_daemon_loop(
        self,
        workspace_process_context: TContext,
        daemon_uuid: str,
        daemon_shutdown_event: Event,
        heartbeat_interval_seconds: int,
        error_interval_seconds: int,
    ):
        from dagster._core.telemetry_upload import uploading_logging_thread

        with uploading_logging_thread():
            daemon_generator = self.core_loop(workspace_process_context, daemon_shutdown_event)

            try:
                while not daemon_shutdown_event.is_set():
                    try:
                        result = check.opt_inst(next(daemon_generator), SerializableErrorInfo)
                        if result:
                            self._errors.appendleft((result, pendulum.now("UTC")))
                    except StopIteration:
                        self._logger.error(
                            "Daemon loop finished without raising an error - daemon loops should"
                            " run forever until they are interrupted."
                        )
                        break
                    except Exception:
                        error_info = serializable_error_info_from_exc_info(sys.exc_info())
                        self._logger.error(
                            "Caught error, daemon loop will restart:\n%s", error_info
                        )
                        self._errors.appendleft((error_info, pendulum.now("UTC")))
                        daemon_generator.close()
                        daemon_generator = self.core_loop(
                            workspace_process_context, daemon_shutdown_event
                        )
                    finally:
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
            finally:
                # cleanup the generator if it was stopped part-way through
                daemon_generator.close()

    def _check_add_heartbeat(
        self,
        instance: DagsterInstance,
        daemon_uuid,
        heartbeat_interval_seconds,
        error_interval_seconds,
    ):
        error_max_time = pendulum.now("UTC").subtract(seconds=error_interval_seconds)

        while len(self._errors):
            _earliest_error, earliest_timestamp = self._errors[-1]
            if earliest_timestamp >= error_max_time:
                break
            self._errors.pop()

        if instance.daemon_skip_heartbeats_without_errors and not self._errors:
            # no errors to report, so we don't write a heartbeat
            return

        curr_time = pendulum.now("UTC")

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
                (
                    "Another %s daemon is still sending heartbeats. You likely have multiple "
                    "daemon processes running at once, which is not supported. "
                    "Last heartbeat daemon id: %s, "
                    "Current daemon_id: %s"
                ),
                daemon_type,
                last_stored_heartbeat.daemon_id,
                daemon_uuid,
            )

        self._last_heartbeat_time = curr_time

        instance.add_daemon_heartbeat(
            DaemonHeartbeat(
                curr_time.float_timestamp,
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
    ) -> TDaemonGenerator:
        """
        Execute the daemon loop, which should be a generator function that never finishes.
        Should periodically yield so that the controller can check for heartbeats. Yields can be either NoneType or a SerializableErrorInfo.

        returns: generator (SerializableErrorInfo).
        """


class IntervalDaemon(DagsterDaemon[TContext], ABC):
    def __init__(self, interval_seconds):
        self.interval_seconds = check.numeric_param(interval_seconds, "interval_seconds")
        super().__init__()

    def core_loop(
        self,
        workspace_process_context: TContext,
        shutdown_event: Event,
    ) -> TDaemonGenerator:
        while True:
            start_time = time.time()
            try:
                yield None  # Heartbeat once at the beginning to kick things off
                yield from self.run_iteration(workspace_process_context)
            except Exception:
                error_info = serializable_error_info_from_exc_info(sys.exc_info())
                self._logger.error("Caught error:\n%s", error_info)
                yield error_info
            while time.time() - start_time < self.interval_seconds:
                shutdown_event.wait(0.5)
                yield None
            yield None

    @abstractmethod
    def run_iteration(self, workspace_process_context: TContext) -> TDaemonGenerator:
        ...


class SchedulerDaemon(DagsterDaemon):
    @classmethod
    def daemon_type(cls):
        return "SCHEDULER"

    def core_loop(
        self,
        workspace_process_context: IWorkspaceProcessContext,
        shutdown_event: Event,
    ) -> TDaemonGenerator:
        scheduler = workspace_process_context.instance.scheduler
        if not isinstance(scheduler, DagsterDaemonScheduler):
            check.failed(f"Expected DagsterDaemonScheduler, got {scheduler}")

        yield from execute_scheduler_iteration_loop(
            workspace_process_context,
            self._logger,
            scheduler.max_catchup_runs,
            scheduler.max_tick_retries,
            shutdown_event,
        )


class SensorDaemon(DagsterDaemon):
    @classmethod
    def daemon_type(cls):
        return "SENSOR"

    def core_loop(
        self,
        workspace_process_context: IWorkspaceProcessContext,
        shutdown_event: Event,
    ) -> TDaemonGenerator:
        yield from execute_sensor_iteration_loop(
            workspace_process_context,
            self._logger,
            shutdown_event,
        )


class BackfillDaemon(IntervalDaemon):
    @classmethod
    def daemon_type(cls):
        return "BACKFILL"

    def run_iteration(
        self,
        workspace_process_context: IWorkspaceProcessContext,
    ) -> TDaemonGenerator:
        yield from execute_backfill_iteration(workspace_process_context, self._logger)


class MonitoringDaemon(IntervalDaemon):
    @classmethod
    def daemon_type(cls):
        return "MONITORING"

    def run_iteration(
        self,
        workspace_process_context: IWorkspaceProcessContext,
    ) -> TDaemonGenerator:
        yield from execute_monitoring_iteration(workspace_process_context, self._logger)

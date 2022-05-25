import logging
import sys
import time
import uuid
from abc import abstractmethod
from collections import deque
from contextlib import AbstractContextManager
from threading import Event
from typing import Callable, ContextManager, Tuple

import pendulum

from dagster import DagsterInstance
from dagster import _check as check
from dagster.core.telemetry import DAEMON_ALIVE, log_action
from dagster.core.workspace import IWorkspace
from dagster.daemon.backfill import execute_backfill_iteration
from dagster.daemon.monitoring import execute_monitoring_iteration
from dagster.daemon.sensor import execute_sensor_iteration_loop
from dagster.daemon.types import DaemonHeartbeat
from dagster.scheduler.scheduler import execute_scheduler_iteration_loop
from dagster.utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info


def get_default_daemon_logger(daemon_name):
    return logging.getLogger(f"dagster.daemon.{daemon_name}")


DAEMON_HEARTBEAT_ERROR_LIMIT = 5  # Show at most 5 errors
TELEMETRY_LOGGING_INTERVAL = 3600 * 24  # Interval (in seconds) at which to log that daemon is alive
_telemetry_daemon_session_id = str(uuid.uuid4())


def get_telemetry_daemon_session_id() -> str:
    return _telemetry_daemon_session_id


class DagsterDaemon(AbstractContextManager):
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
    def daemon_type(cls):
        """
        returns: str
        """

    def __exit__(self, _exception_type, _exception_value, _traceback):
        pass

    def run_daemon_loop(
        self,
        daemon_uuid: str,
        daemon_shutdown_event: Event,
        context_fn: Callable[[], ContextManager[Tuple[DagsterInstance, IWorkspace]]],
        heartbeat_interval_seconds: int,
        error_interval_seconds: int,
    ):
        from dagster.core.telemetry_upload import uploading_logging_thread

        # Each loop runs in its own thread with its own instance and IWorkspace
        with context_fn() as (instance, workspace):
            with uploading_logging_thread():
                check.inst_param(workspace, "workspace", IWorkspace)

                daemon_generator = self.core_loop(instance, workspace)

                try:
                    while not daemon_shutdown_event.is_set():
                        try:
                            result = check.opt_inst(next(daemon_generator), SerializableErrorInfo)
                            if result:
                                self._errors.appendleft((result, pendulum.now("UTC")))
                        except StopIteration:
                            self._logger.error(
                                "Daemon loop finished without raising an error - daemon loops should run forever until they are interrupted."
                            )
                            break
                        except Exception:
                            error_info = serializable_error_info_from_exc_info(sys.exc_info())
                            self._logger.error(
                                "Caught error, daemon loop will restart:\n%s", error_info
                            )
                            self._errors.appendleft((error_info, pendulum.now("UTC")))
                            daemon_generator.close()
                            daemon_generator = self.core_loop(instance, workspace)
                        finally:
                            try:
                                self._check_add_heartbeat(
                                    instance,
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
        self, instance, daemon_uuid, heartbeat_interval_seconds, error_interval_seconds
    ):
        error_max_time = pendulum.now("UTC").subtract(seconds=error_interval_seconds)

        while len(self._errors):
            _earliest_error, earliest_timestamp = self._errors[-1]
            if earliest_timestamp >= error_max_time:
                break
            self._errors.pop()

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
    def core_loop(self, instance, workspace):
        """
        Execute the daemon loop, which should be a generator function that never finishes.
        Should periodically yield so that the controller can check for heartbeats. Yields can be either NoneType or a SerializableErrorInfo.

        returns: generator (SerializableErrorInfo).
        """


class IntervalDaemon(DagsterDaemon):
    def __init__(self, interval_seconds):
        self.interval_seconds = check.numeric_param(interval_seconds, "interval_seconds")
        super().__init__()

    def core_loop(self, instance, workspace):
        while True:
            start_time = time.time()
            # Clear out the workspace locations after each iteration
            workspace.cleanup()
            try:
                yield from self.run_iteration(instance, workspace)
            except Exception:
                error_info = serializable_error_info_from_exc_info(sys.exc_info())
                self._logger.error("Caught error:\n%s", error_info)
                yield error_info
            while time.time() - start_time < self.interval_seconds:
                yield
                time.sleep(0.5)
            yield

    @abstractmethod
    def run_iteration(self, instance, workspace):
        pass


class SchedulerDaemon(DagsterDaemon):
    @classmethod
    def daemon_type(cls):
        return "SCHEDULER"

    def core_loop(self, instance, workspace):
        yield from execute_scheduler_iteration_loop(
            instance,
            workspace,
            self._logger,
            instance.scheduler.max_catchup_runs,
            instance.scheduler.max_tick_retries,
        )


class SensorDaemon(DagsterDaemon):
    @classmethod
    def daemon_type(cls):
        return "SENSOR"

    def core_loop(self, instance, workspace):
        yield from execute_sensor_iteration_loop(instance, workspace, self._logger)


class BackfillDaemon(IntervalDaemon):
    @classmethod
    def daemon_type(cls):
        return "BACKFILL"

    def run_iteration(self, instance, workspace):
        yield from execute_backfill_iteration(instance, workspace, self._logger)


class MonitoringDaemon(IntervalDaemon):
    @classmethod
    def daemon_type(cls):
        return "MONITORING"

    def run_iteration(self, instance, workspace):
        yield from execute_monitoring_iteration(instance, workspace, self._logger)

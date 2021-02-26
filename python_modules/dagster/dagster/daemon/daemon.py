import logging
import sys
from abc import abstractclassmethod, abstractmethod
from contextlib import AbstractContextManager

import pendulum
from dagster import DagsterInstance, check
from dagster.core.definitions.sensor import DEFAULT_SENSOR_DAEMON_INTERVAL
from dagster.daemon.backfill import execute_backfill_iteration
from dagster.daemon.types import DaemonHeartbeat
from dagster.scheduler import execute_scheduler_iteration
from dagster.scheduler.sensor import execute_sensor_iteration_loop
from dagster.utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info
from dagster.utils.log import default_format_string

# Interval at which heartbeats are posted
DAEMON_HEARTBEAT_INTERVAL_SECONDS = 30


def _mockable_localtime(_):
    now_time = pendulum.now()
    return now_time.timetuple()


def get_default_daemon_logger(daemon_name):
    handler = logging.StreamHandler(sys.stdout)
    logger = logging.getLogger(daemon_name)
    logger.setLevel(logging.INFO)
    logger.handlers = [handler]

    formatter = logging.Formatter(default_format_string(), "%Y-%m-%d %H:%M:%S")

    formatter.converter = _mockable_localtime

    handler.setFormatter(formatter)
    return logger


class CompletedIteration(object):
    pass


class DagsterDaemon(AbstractContextManager):
    def __init__(self, interval_seconds):
        self._logger = get_default_daemon_logger(type(self).__name__)
        self.interval_seconds = check.numeric_param(interval_seconds, "interval_seconds")

        self._last_iteration_time = None
        self._last_heartbeat_time = None
        self._current_iteration_exceptions = None
        self._last_iteration_exceptions = None

        self._first_error_logged = False

    @abstractclassmethod
    def daemon_type(cls):
        """
        returns: str
        """

    def __exit__(self, _exception_type, _exception_value, _traceback):
        pass

    def run_loop(self, daemon_uuid, daemon_shutdown_event, grpc_server_registry, until=None):
        # Each loop runs in its own thread with its own instance
        with DagsterInstance.get() as instance:
            while not daemon_shutdown_event.is_set() and (not until or pendulum.now("UTC") < until):
                curr_time = pendulum.now("UTC")
                if (
                    not self._last_iteration_time
                    or (curr_time - self._last_iteration_time).total_seconds()
                    >= self.interval_seconds
                ):
                    self._last_iteration_time = curr_time
                    self._run_iteration(
                        instance, daemon_uuid, daemon_shutdown_event, grpc_server_registry, until
                    )

                daemon_shutdown_event.wait(0.5)

    def _run_iteration(
        self, instance, daemon_uuid, daemon_shutdown_event, grpc_server_registry, until=None
    ):
        # Build a list of any exceptions encountered during the iteration.
        # Once the iteration completes, this is copied to last_iteration_exceptions
        # which is used in the heartbeats. This guarantees that heartbeats contain the full
        # list of errors raised.
        self._current_iteration_exceptions = []
        daemon_generator = self.run_iteration(instance, daemon_shutdown_event, grpc_server_registry)

        while not until or pendulum.now("UTC") < until:
            try:
                result = check.opt_inst(
                    next(daemon_generator), tuple([SerializableErrorInfo, CompletedIteration])
                )
                if isinstance(result, CompletedIteration):
                    self._last_iteration_exceptions = self._current_iteration_exceptions
                    self._current_iteration_exceptions = []
                elif result:
                    self._current_iteration_exceptions.append(result)
            except StopIteration:
                self._last_iteration_exceptions = self._current_iteration_exceptions
                break
            except Exception:  # pylint: disable=broad-except
                error_info = serializable_error_info_from_exc_info(sys.exc_info())
                self._logger.error("Caught error:\n{}".format(error_info))
                self._current_iteration_exceptions.append(error_info)
                self._last_iteration_exceptions = self._current_iteration_exceptions
                break
            finally:
                self._check_add_heartbeat(instance, daemon_uuid)

    def _check_add_heartbeat(self, instance, daemon_uuid):
        # Always log a heartbeat after the first time an iteration returns an error to make sure we
        # don't incorrectly say the daemon is healthy
        first_time_logging_error = self._last_iteration_exceptions and not self._first_error_logged

        curr_time = pendulum.now("UTC")
        if not first_time_logging_error and (
            self._last_heartbeat_time
            and (curr_time - self._last_heartbeat_time).total_seconds()
            < DAEMON_HEARTBEAT_INTERVAL_SECONDS
        ):
            return

        if first_time_logging_error:
            self._first_error_logged = True

        daemon_type = self.daemon_type()

        last_stored_heartbeat = instance.get_daemon_heartbeats().get(daemon_type)
        if (
            self._last_heartbeat_time  # not the first heartbeat
            and last_stored_heartbeat
            and last_stored_heartbeat.daemon_id != daemon_uuid
        ):
            self._logger.warning(
                "Taking over from another {} daemon process. If this "
                "message reoccurs, you may have multiple daemons running which is not supported. "
                "Last heartbeat daemon id: {}, "
                "Current daemon_id: {}".format(
                    daemon_type,
                    last_stored_heartbeat.daemon_id,
                    daemon_uuid,
                )
            )

        self._last_heartbeat_time = curr_time

        instance.add_daemon_heartbeat(
            DaemonHeartbeat(
                curr_time.float_timestamp,
                daemon_type,
                daemon_uuid,
                errors=self._last_iteration_exceptions,
            )
        )

    @abstractmethod
    def run_iteration(self, instance, daemon_shutdown_event, grpc_server_registry):
        """
        Execute the daemon. In order to avoid blocking the controller thread for extended periods,
        daemons can yield control during this method. Yields can be either NoneType or a
        SerializableErrorInfo

        returns: generator (SerializableErrorInfo).
        """


class SchedulerDaemon(DagsterDaemon):
    def __init__(
        self,
        interval_seconds,
        max_catchup_runs,
    ):
        super(SchedulerDaemon, self).__init__(interval_seconds)
        self._max_catchup_runs = max_catchup_runs

    @staticmethod
    def create_from_instance(instance):
        max_catchup_runs = instance.scheduler.max_catchup_runs

        from dagster.daemon.controller import DEFAULT_DAEMON_INTERVAL_SECONDS

        return SchedulerDaemon(
            interval_seconds=DEFAULT_DAEMON_INTERVAL_SECONDS,
            max_catchup_runs=max_catchup_runs,
        )

    @classmethod
    def daemon_type(cls):
        return "SCHEDULER"

    def run_iteration(self, instance, daemon_shutdown_event, grpc_server_registry):
        yield from execute_scheduler_iteration(
            instance, grpc_server_registry, self._logger, self._max_catchup_runs
        )


class SensorDaemon(DagsterDaemon):
    @staticmethod
    def create_from_instance(instance):
        sensor_settings = instance.get_settings("sensor_settings") or {}
        return SensorDaemon(
            interval_seconds=sensor_settings.get(
                "interval_seconds", DEFAULT_SENSOR_DAEMON_INTERVAL
            ),
        )

    @classmethod
    def daemon_type(cls):
        return "SENSOR"

    def run_iteration(self, instance, daemon_shutdown_event, grpc_server_registry):
        yield from execute_sensor_iteration_loop(
            instance, grpc_server_registry, self._logger, daemon_shutdown_event
        )


class BackfillDaemon(DagsterDaemon):
    @staticmethod
    def create_from_instance(_instance):
        from dagster.daemon.controller import DEFAULT_DAEMON_INTERVAL_SECONDS

        return BackfillDaemon(interval_seconds=DEFAULT_DAEMON_INTERVAL_SECONDS)

    @classmethod
    def daemon_type(cls):
        return "BACKFILL"

    def run_iteration(self, instance, daemon_shutdown_event, grpc_server_registry):
        yield from execute_backfill_iteration(instance, grpc_server_registry, self._logger)

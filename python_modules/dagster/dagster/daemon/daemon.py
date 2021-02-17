import logging
import sys
from abc import abstractclassmethod, abstractmethod

import pendulum
from dagster import DagsterInstance, check
from dagster.core.definitions.sensor import DEFAULT_SENSOR_DAEMON_INTERVAL
from dagster.daemon.backfill import execute_backfill_iteration
from dagster.daemon.types import DaemonHeartbeat
from dagster.scheduler import execute_scheduler_iteration
from dagster.scheduler.sensor import execute_sensor_iteration
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


class DagsterDaemon:
    def __init__(self, interval_seconds):
        self._logger = get_default_daemon_logger(type(self).__name__)
        self.interval_seconds = check.numeric_param(interval_seconds, "interval_seconds")

        self._last_iteration_time = None
        self._last_heartbeat_time = None
        self._current_iteration_exceptions = None
        self._last_iteration_exceptions = None

    @abstractclassmethod
    def daemon_type(cls):
        """
        returns: str
        """

    def run_loop(self, daemon_uuid, daemon_shutdown_event):
        # Each loop runs in its own thread with its own instance
        with DagsterInstance.get() as instance:
            while not daemon_shutdown_event.is_set():
                curr_time = pendulum.now("UTC")

                if (
                    not self._last_iteration_time
                    or (curr_time - self._last_iteration_time).total_seconds()
                    >= self.interval_seconds
                ):
                    self._last_iteration_time = curr_time
                    self._run_iteration(instance, curr_time, daemon_uuid)

                daemon_shutdown_event.wait(0.5)

    def _run_iteration(self, instance, curr_time, daemon_uuid):
        # Build a list of any exceptions encountered during the iteration.
        # Once the iteration completes, this is copied to last_iteration_exceptions
        # which is used in the heartbeats. This guarantees that heartbeats contain the full
        # list of errors raised.
        self._current_iteration_exceptions = []
        first_iteration = not self._last_heartbeat_time

        daemon_generator = self.run_iteration(instance)

        while True:
            try:
                error_info = check.opt_inst(next(daemon_generator), SerializableErrorInfo)
                if error_info:
                    self._current_iteration_exceptions.append(error_info)
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
                if not first_iteration:
                    # wait until first iteration completes, since we report any errors from the previous
                    # iteration in the heartbeat. After the first iteration, start logging a heartbeat
                    # every time the generator yields.
                    self._check_add_heartbeat(instance, curr_time, daemon_uuid)

        if first_iteration:
            self._check_add_heartbeat(instance, curr_time, daemon_uuid)

    def _check_add_heartbeat(self, instance, curr_time, daemon_uuid):
        if (
            self._last_heartbeat_time
            and (curr_time - self._last_heartbeat_time).total_seconds()
            < DAEMON_HEARTBEAT_INTERVAL_SECONDS
        ):
            return

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
    def run_iteration(self, instance):
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

    def run_iteration(self, instance):
        return execute_scheduler_iteration(instance, self._logger, self._max_catchup_runs)


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

    def run_iteration(self, instance):
        return execute_sensor_iteration(instance, self._logger)


class BackfillDaemon(DagsterDaemon):
    @staticmethod
    def create_from_instance(_instance):
        from dagster.daemon.controller import DEFAULT_DAEMON_INTERVAL_SECONDS

        return BackfillDaemon(interval_seconds=DEFAULT_DAEMON_INTERVAL_SECONDS)

    @classmethod
    def daemon_type(cls):
        return "BACKFILL"

    def run_iteration(self, instance):
        return execute_backfill_iteration(instance, self._logger)

import logging
import sys
from abc import abstractclassmethod, abstractmethod

import pendulum
from dagster import DagsterInstance, check
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
    def __init__(self, instance, interval_seconds, daemon_uuid, thread_shutdown_event):
        self._instance = check.inst_param(instance, "instance", DagsterInstance)
        self._logger = get_default_daemon_logger(type(self).__name__)
        self.interval_seconds = check.int_param(interval_seconds, "interval_seconds")
        self._daemon_uuid = check.str_param(daemon_uuid, "daemon_uuid")
        self._thread_shutdown_event = thread_shutdown_event

        self._last_iteration_time = None
        self._last_heartbeat_time = None
        self._current_iteration_exceptions = None
        self._last_iteration_exceptions = None

    @abstractclassmethod
    def daemon_type(cls):
        """
        returns: str
        """

    def run_loop(self):
        while not self._thread_shutdown_event.is_set():
            curr_time = pendulum.now("UTC")

            if (
                not self._last_iteration_time
                or (curr_time - self._last_iteration_time).total_seconds() >= self.interval_seconds
            ):
                self._last_iteration_time = curr_time
                self._run_iteration(curr_time)

            self._thread_shutdown_event.wait(0.5)

    def _run_iteration(self, curr_time):
        # Build a list of any exceptions encountered during the iteration.
        # Once the iteration completes, this is copied to last_iteration_exceptions
        # which is used in the heartbeats. This guarantees that heartbeats contain the full
        # list of errors raised.
        self._current_iteration_exceptions = []
        first_iteration = not self._last_heartbeat_time

        daemon_generator = self.run_iteration()

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
                    self._check_add_heartbeat(curr_time)

        if first_iteration:
            self._check_add_heartbeat(curr_time)

    def _check_add_heartbeat(self, curr_time):
        if (
            self._last_heartbeat_time
            and (curr_time - self._last_heartbeat_time).total_seconds()
            < DAEMON_HEARTBEAT_INTERVAL_SECONDS
        ):
            return

        daemon_type = self.daemon_type()

        last_stored_heartbeat = self._instance.get_daemon_heartbeats().get(daemon_type)
        if (
            self._last_heartbeat_time  # not the first heartbeat
            and last_stored_heartbeat
            and last_stored_heartbeat.daemon_id != self._daemon_uuid
        ):
            self._logger.warning(
                "Taking over from another {} daemon process. If this "
                "message reoccurs, you may have multiple daemons running which is not supported. "
                "Last heartbeat daemon id: {}, "
                "Current daemon_id: {}".format(
                    daemon_type, last_stored_heartbeat.daemon_id, self._daemon_uuid,
                )
            )

        self._last_heartbeat_time = curr_time

        self._instance.add_daemon_heartbeat(
            DaemonHeartbeat(
                curr_time.float_timestamp,
                daemon_type,
                self._daemon_uuid,
                errors=self._last_iteration_exceptions,
            )
        )

    @abstractmethod
    def run_iteration(self):
        """
        Execute the daemon. In order to avoid blocking the controller thread for extended periods,
        daemons can yield control during this method. Yields can be either NoneType or a
        SerializableErrorInfo

        returns: generator (SerializableErrorInfo).
        """


class SchedulerDaemon(DagsterDaemon):
    def __init__(
        self, instance, interval_seconds, max_catchup_runs, daemon_uuid, thread_shutdown_event
    ):
        super(SchedulerDaemon, self).__init__(
            instance, interval_seconds, daemon_uuid, thread_shutdown_event
        )
        self._max_catchup_runs = max_catchup_runs

    @classmethod
    def daemon_type(cls):
        return "SCHEDULER"

    def run_iteration(self):
        return execute_scheduler_iteration(self._instance, self._logger, self._max_catchup_runs)


class SensorDaemon(DagsterDaemon):
    @classmethod
    def daemon_type(cls):
        return "SENSOR"

    def run_iteration(self):
        return execute_sensor_iteration(self._instance, self._logger)

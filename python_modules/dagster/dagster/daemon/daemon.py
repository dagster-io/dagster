import logging
import sys
from abc import abstractclassmethod, abstractmethod
from contextlib import AbstractContextManager

import pendulum
from dagster import DagsterInstance, check
from dagster.cli.workspace.workspace import IWorkspace
from dagster.core.definitions.sensor import DEFAULT_SENSOR_DAEMON_INTERVAL
from dagster.daemon.backfill import execute_backfill_iteration
from dagster.daemon.sensor import execute_sensor_iteration_loop
from dagster.daemon.types import DaemonHeartbeat
from dagster.scheduler import execute_scheduler_iteration
from dagster.utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info
from dagster.utils.log import default_format_string


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


DAEMON_HEARTBEAT_ERROR_LIMIT = 5  # Show at most 5 errors


class DagsterDaemon(AbstractContextManager):
    def __init__(self, interval_seconds):
        self._logger = get_default_daemon_logger(type(self).__name__)
        self.interval_seconds = check.numeric_param(interval_seconds, "interval_seconds")

        self._last_iteration_time = None
        self._last_heartbeat_time = None
        self._start_loop_time = None
        self._errors = []  # (SerializableErrorInfo, timestamp) tuples

        self._first_error_logged = False

    @abstractclassmethod
    def daemon_type(cls):
        """
        returns: str
        """

    def __exit__(self, _exception_type, _exception_value, _traceback):
        pass

    def run_loop(
        self,
        daemon_uuid,
        daemon_shutdown_event,
        gen_workspace,
        heartbeat_interval_seconds,
        error_interval_seconds,
        until=None,
    ):
        # Each loop runs in its own thread with its own instance and IWorkspace
        with DagsterInstance.get() as instance:
            with gen_workspace(instance) as workspace:
                check.inst_param(workspace, "workspace", IWorkspace)

                self._start_loop_time = pendulum.now("UTC")

                while not daemon_shutdown_event.is_set() and (
                    not until or pendulum.now("UTC") < until
                ):
                    curr_time = pendulum.now("UTC")
                    if (
                        not self._last_iteration_time
                        or (curr_time - self._last_iteration_time).total_seconds()
                        >= self.interval_seconds
                    ):
                        self._last_iteration_time = curr_time
                        self._run_iteration(
                            instance,
                            daemon_uuid,
                            daemon_shutdown_event,
                            workspace,
                            heartbeat_interval_seconds,
                            error_interval_seconds,
                            until,
                        )

                    self._check_add_heartbeat(
                        instance, daemon_uuid, heartbeat_interval_seconds, error_interval_seconds
                    )
                    daemon_shutdown_event.wait(0.5)

    def _run_iteration(
        self,
        instance,
        daemon_uuid,
        daemon_shutdown_event,
        workspace,
        heartbeat_interval_seconds,
        error_interval_seconds,
        until=None,
    ):
        # Clear out the workspace locations after each iteration
        workspace.cleanup()

        daemon_generator = self.run_iteration(instance, workspace)

        try:
            while (not daemon_shutdown_event.is_set()) and (
                not until or pendulum.now("UTC") < until
            ):
                try:
                    result = check.opt_inst(next(daemon_generator), SerializableErrorInfo)
                    if result:
                        self._errors.append((result, pendulum.now("UTC")))
                except StopIteration:
                    break
                except Exception:  # pylint: disable=broad-except
                    error_info = serializable_error_info_from_exc_info(sys.exc_info())
                    self._logger.error("Caught error:\n{}".format(error_info))
                    self._errors.append((error_info, pendulum.now("UTC")))
                    break
                finally:
                    try:
                        self._check_add_heartbeat(
                            instance,
                            daemon_uuid,
                            heartbeat_interval_seconds,
                            error_interval_seconds,
                        )
                    except Exception:  # pylint: disable=broad-except
                        self._logger.error(
                            "Failed to add heartbeat: \n{}".format(
                                serializable_error_info_from_exc_info(sys.exc_info())
                            )
                        )

        finally:
            # cleanup the generator if it was stopped part-way through
            daemon_generator.close()

    def _check_add_heartbeat(
        self, instance, daemon_uuid, heartbeat_interval_seconds, error_interval_seconds
    ):
        error_max_time = pendulum.now("UTC").subtract(seconds=error_interval_seconds)

        self._errors = self._errors[:DAEMON_HEARTBEAT_ERROR_LIMIT]

        self._errors = [
            (error, timestamp) for (error, timestamp) in self._errors if timestamp >= error_max_time
        ]

        curr_time = pendulum.now("UTC")

        heartbeat_compare_time = (
            self._last_heartbeat_time if self._last_heartbeat_time else self._start_loop_time
        )

        if (curr_time - heartbeat_compare_time).total_seconds() < heartbeat_interval_seconds:
            return

        daemon_type = self.daemon_type()

        last_stored_heartbeat = instance.get_daemon_heartbeats().get(daemon_type)
        if (
            self._last_heartbeat_time
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
                errors=[error for (error, timestamp) in self._errors],
            )
        )

    @abstractmethod
    def run_iteration(self, instance, workspace):
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

    def run_iteration(self, instance, workspace):
        yield from execute_scheduler_iteration(
            instance, workspace, self._logger, self._max_catchup_runs
        )


class SensorDaemon(DagsterDaemon):
    @staticmethod
    def create_from_instance(_instance):
        return SensorDaemon(interval_seconds=DEFAULT_SENSOR_DAEMON_INTERVAL)

    @classmethod
    def daemon_type(cls):
        return "SENSOR"

    def run_iteration(self, instance, workspace):
        yield from execute_sensor_iteration_loop(instance, workspace, self._logger)


class BackfillDaemon(DagsterDaemon):
    @staticmethod
    def create_from_instance(_instance):
        from dagster.daemon.controller import DEFAULT_DAEMON_INTERVAL_SECONDS

        return BackfillDaemon(interval_seconds=DEFAULT_DAEMON_INTERVAL_SECONDS)

    @classmethod
    def daemon_type(cls):
        return "BACKFILL"

    def run_iteration(self, instance, workspace):
        yield from execute_backfill_iteration(instance, workspace, self._logger)

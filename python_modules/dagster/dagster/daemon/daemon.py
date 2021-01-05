import logging
import sys
from abc import abstractclassmethod, abstractmethod

import pendulum
from dagster import DagsterInstance, check
from dagster.daemon.types import DaemonType
from dagster.scheduler import execute_scheduler_iteration
from dagster.scheduler.sensor import execute_sensor_iteration
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


class DagsterDaemon:
    def __init__(self, instance, interval_seconds):
        self._instance = check.inst_param(instance, "instance", DagsterInstance)
        self._logger = get_default_daemon_logger(type(self).__name__)
        self.interval_seconds = check.int_param(interval_seconds, "interval_seconds")
        self.last_iteration_time = None
        self.last_iteration_exception = None

    @abstractclassmethod
    def daemon_type(cls):
        """
        returns: DaemonType
        """

    @abstractmethod
    def run_iteration(self):
        """
        Execute the daemon. In order to avoid blocking the controller thread for extended periods,
        daemons can yield control during this method.

        returns: generator (NoneType)
        """


class SchedulerDaemon(DagsterDaemon):
    def __init__(self, instance, interval_seconds, max_catchup_runs):
        super(SchedulerDaemon, self).__init__(instance, interval_seconds)
        self._max_catchup_runs = max_catchup_runs

    @classmethod
    def daemon_type(cls):
        return DaemonType.SCHEDULER

    def run_iteration(self):
        return execute_scheduler_iteration(self._instance, self._logger, self._max_catchup_runs)


class SensorDaemon(DagsterDaemon):
    @classmethod
    def daemon_type(cls):
        return DaemonType.SENSOR

    def run_iteration(self):
        return execute_sensor_iteration(self._instance, self._logger)

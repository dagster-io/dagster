import logging
import sys
import time

import pendulum
from dagster import DagsterEvent, DagsterEventType, DagsterInstance, check
from dagster.core.events.log import DagsterEventRecord
from dagster.core.storage.pipeline_run import PipelineRunStatus, PipelineRunsFilter
from dagster.utils.backcompat import experimental
from dagster.utils.external import external_pipeline_from_run
from dagster.utils.log import default_format_string

IN_PROGRESS_STATUSES = [
    PipelineRunStatus.NOT_STARTED,
    PipelineRunStatus.STARTED,
]


def _mockable_localtime(_):
    now_time = pendulum.now()
    return now_time.timetuple()


def get_default_daemon_logger(logging_level=logging.INFO):
    handler = logging.StreamHandler(sys.stdout)
    logger = logging.getLogger("dagster-daemon")
    logger.setLevel(logging_level)
    logger.handlers = [handler]

    formatter = logging.Formatter(default_format_string(), "%Y-%m-%d %H:%M:%S")

    formatter.converter = _mockable_localtime

    handler.setFormatter(formatter)
    return logger


class QueuedRunCoordinatorDaemon:
    """
    Used with the QueuedRunCoordinator on the instance. This process finds queued runs from the run
    store and launches them.
    """

    @experimental
    def __init__(
        self,
        instance,
        max_concurrent_runs=10,
        logger=get_default_daemon_logger(logging_level=logging.DEBUG),
    ):
        self._instance = check.inst_param(instance, "instance", DagsterInstance)
        self._max_concurrent_runs = check.int_param(max_concurrent_runs, "max_concurrent_runs")
        self._logger = logger

    def run(self, interval_seconds=2):
        """
        Run the coordinator daemon

        Arguments:
            interval_seconds (float): time in seconds to wait between dequeuing attempts
        """
        check.numeric_param(interval_seconds, "interval_seconds")

        while True:
            self.attempt_to_launch_runs()
            time.sleep(interval_seconds)

    def attempt_to_launch_runs(self):
        in_progress = self._count_in_progress_runs()
        max_runs_to_launch = self._max_concurrent_runs - in_progress

        # Possibly under 0 if runs were launched without queuing
        if max_runs_to_launch <= 0:
            self._logger.debug(
                "{} runs are currently in progress. Maximum is {}, won't launch more.".format(
                    in_progress, self._max_concurrent_runs
                )
            )
            return

        queued_runs = self._get_queued_runs(limit=max_runs_to_launch)

        if not queued_runs:
            self._logger.debug("Poll returned no queued runs.")
        else:
            self._logger.debug("Retrieved {} queued runs to launch.".format(len(queued_runs)))

        for run in queued_runs:
            with external_pipeline_from_run(run) as external_pipeline:
                enqueued_event = DagsterEvent(
                    event_type_value=DagsterEventType.PIPELINE_DEQUEUED.value,
                    pipeline_name=run.pipeline_name,
                )
                event_record = DagsterEventRecord(
                    message="",
                    user_message="",
                    level=logging.INFO,
                    pipeline_name=run.pipeline_name,
                    run_id=run.run_id,
                    error_info=None,
                    timestamp=time.time(),
                    dagster_event=enqueued_event,
                )
                self._instance.handle_new_event(event_record)

                self._instance.launch_run(run.run_id, external_pipeline)

    def _get_queued_runs(self, limit=None):
        queued_runs_filter = PipelineRunsFilter(status=PipelineRunStatus.QUEUED)

        runs = self._instance.get_runs(filters=queued_runs_filter, limit=limit)
        assert len(runs) <= limit
        return runs

    def _count_in_progress_runs(self):
        num_runs = 0

        # NOTE: this can be reduced to a single query if PipelineRunsFilters can take multiple statuses
        for status in IN_PROGRESS_STATUSES:
            runs_filter = PipelineRunsFilter(status=status)
            num_runs += self._instance.get_runs_count(filters=runs_filter)

        return num_runs

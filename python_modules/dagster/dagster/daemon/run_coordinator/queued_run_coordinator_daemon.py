import logging
import time
from collections import defaultdict

from dagster import DagsterEvent, DagsterEventType, check
from dagster.core.events.log import DagsterEventRecord
from dagster.core.storage.pipeline_run import (
    IN_PROGRESS_RUN_STATUSES,
    PipelineRun,
    PipelineRunStatus,
    PipelineRunsFilter,
)
from dagster.core.storage.tags import PRIORITY_TAG
from dagster.daemon.daemon import DagsterDaemon
from dagster.daemon.types import DaemonType
from dagster.utils.backcompat import experimental
from dagster.utils.external import external_pipeline_from_run


class _TagConcurrencyLimitsCounter:
    """
    Helper object that keeps track of when the tag concurrency limits are met
    """

    def __init__(self, tag_concurrency_limits, in_progress_runs):
        check.opt_list_param(tag_concurrency_limits, "tag_concurrency_limits", of_type=dict)
        check.list_param(in_progress_runs, "in_progress_runs", of_type=PipelineRun)

        # convert currency_limits to dict
        self._tag_concurrency_limits = {}
        for tag_limit in tag_concurrency_limits:
            self._tag_concurrency_limits[(tag_limit["key"], tag_limit.get("value"))] = tag_limit[
                "limit"
            ]

        # initialize counters based on current in progress runs
        self._in_progress_limit_counts = defaultdict(lambda: 0)
        for run in in_progress_runs:
            limited_tags = self._get_limited_tags(run)
            for tag_value in limited_tags:
                self._in_progress_limit_counts[tag_value] += 1

    def _get_limited_tags(self, run):
        """
        Returns the tags on the run which match one of the limits
        """
        tags = []
        for tag_key, tag_value in run.tags.items():
            # Check for rules which match either just the tag key, or rules that match on both the
            # key and value. Note that both may apply.
            if (tag_key, None) in self._tag_concurrency_limits:
                tags.append((tag_key, None))
            if (tag_key, tag_value) in self._tag_concurrency_limits:
                tags.append((tag_key, tag_value))
        return tags

    def is_run_blocked(self, run):
        """
        True if there are in progress runs which are blocking this run based on tag limits
        """
        limited_tags = self._get_limited_tags(run)
        return any(
            tag_value
            for tag_value in limited_tags
            if self._in_progress_limit_counts[tag_value] >= self._tag_concurrency_limits[tag_value]
        )

    def update_counters_with_launched_run(self, run):
        """
        Add a new in progress run to the counters
        """
        limited_tags = self._get_limited_tags(run)
        for tag_value in limited_tags:
            self._in_progress_limit_counts[tag_value] += 1


class QueuedRunCoordinatorDaemon(DagsterDaemon):
    """
    Used with the QueuedRunCoordinator on the instance. This process finds queued runs from the run
    store and launches them.
    """

    @experimental
    def __init__(
        self, instance, interval_seconds, max_concurrent_runs, tag_concurrency_limits=None
    ):
        super(QueuedRunCoordinatorDaemon, self).__init__(instance, interval_seconds)
        self._max_concurrent_runs = check.int_param(max_concurrent_runs, "max_concurrent_runs")
        self._tag_concurrency_limits = check.opt_list_param(
            tag_concurrency_limits, "tag_concurrency_limits"
        )

    @classmethod
    def daemon_type(cls):
        return DaemonType.QUEUED_RUN_COORDINATOR

    def run_iteration(self):
        in_progress_runs = self._get_in_progress_runs()
        max_runs_to_launch = self._max_concurrent_runs - len(in_progress_runs)

        # Possibly under 0 if runs were launched without queuing
        if max_runs_to_launch <= 0:
            self._logger.info(
                "{} runs are currently in progress. Maximum is {}, won't launch more.".format(
                    len(in_progress_runs), self._max_concurrent_runs
                )
            )
            return

        queued_runs = self._get_queued_runs()

        if not queued_runs:
            self._logger.info("Poll returned no queued runs.")
        else:
            self._logger.info("Retrieved {} queued runs, checking limits.".format(len(queued_runs)))

        # place in order
        sorted_runs = self._priority_sort(queued_runs)

        # launch until blocked by limit rules
        num_dequeued_runs = 0
        tag_concurrency_limits_counter = _TagConcurrencyLimitsCounter(
            self._tag_concurrency_limits, in_progress_runs
        )
        for run in sorted_runs:
            if num_dequeued_runs >= max_runs_to_launch:
                break

            if tag_concurrency_limits_counter.is_run_blocked(run):
                continue

            self._dequeue_run(run)
            tag_concurrency_limits_counter.update_counters_with_launched_run(run)
            num_dequeued_runs += 1

        self._logger.info("Launched {} runs.".format(num_dequeued_runs))

    def _get_queued_runs(self):
        queued_runs_filter = PipelineRunsFilter(statuses=[PipelineRunStatus.QUEUED])

        # Reversed for fifo ordering
        # Note: should add a maximum fetch limit https://github.com/dagster-io/dagster/issues/3339
        runs = self._instance.get_runs(filters=queued_runs_filter)[::-1]
        return runs

    def _get_in_progress_runs(self):
        # Note: should add a maximum fetch limit https://github.com/dagster-io/dagster/issues/3339
        return self._instance.get_runs(
            filters=PipelineRunsFilter(statuses=IN_PROGRESS_RUN_STATUSES)
        )

    def _priority_sort(self, runs):
        def get_priority(run):
            priority_tag_value = run.tags.get(PRIORITY_TAG, "0")
            try:
                return int(priority_tag_value)
            except ValueError:
                return 0

        # sorted is stable, so fifo is maintained
        return sorted(runs, key=get_priority, reverse=True)

    def _dequeue_run(self, run):
        with external_pipeline_from_run(run) as external_pipeline:
            dequeued_event = DagsterEvent(
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
                dagster_event=dequeued_event,
            )
            self._instance.handle_new_event(event_record)

            self._instance.launch_run(run.run_id, external_pipeline)

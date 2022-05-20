import logging
import time
from typing import Any, Dict, List, NamedTuple, Optional

from dagster import DagsterEvent, DagsterEventType, IntSource, String
from dagster import _check as check
from dagster.builtins import Bool
from dagster.config import Field
from dagster.config.config_type import Array, Noneable, ScalarUnion
from dagster.config.field_utils import Shape
from dagster.core.events.log import EventLogEntry
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.serdes import ConfigurableClass, ConfigurableClassData

from .base import RunCoordinator, SubmitRunContext


class RunQueueConfig(
    NamedTuple(
        "_RunQueueConfig",
        [("max_concurrent_runs", int), ("tag_concurrency_limits", Optional[List[Dict[str, Any]]])],
    )
):
    pass


class QueuedRunCoordinator(RunCoordinator, ConfigurableClass):
    """
    Enqueues runs via the run storage, to be deqeueued by the Dagster Daemon process. Requires
    the Dagster Daemon process to be alive in order for runs to be launched.
    """

    def __init__(
        self,
        max_concurrent_runs=None,
        tag_concurrency_limits=None,
        dequeue_interval_seconds=None,
        inst_data=None,
    ):
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self._max_concurrent_runs = check.opt_int_param(
            max_concurrent_runs, "max_concurrent_runs", 10
        )
        check.invariant(
            self._max_concurrent_runs >= -1,
            "Negative values other than -1 (which disables the limit) for max_concurrent_runs are disallowed.",
        )
        self._tag_concurrency_limits = check.opt_list_param(
            tag_concurrency_limits,
            "tag_concurrency_limits",
        )
        self._dequeue_interval_seconds = check.opt_int_param(
            dequeue_interval_seconds, "dequeue_interval_seconds", 5
        )

        super().__init__()

    @property
    def inst_data(self):
        return self._inst_data

    def get_run_queue_config(self):
        return RunQueueConfig(
            max_concurrent_runs=self._max_concurrent_runs,
            tag_concurrency_limits=self._tag_concurrency_limits,
        )

    @property
    def dequeue_interval_seconds(self):
        return self._dequeue_interval_seconds

    @classmethod
    def config_type(cls):
        return {
            "max_concurrent_runs": Field(
                config=IntSource,
                is_required=False,
                description="The maximum number of runs that are allowed to be in progress at once. "
                "Defaults to 10. Set to -1 to disable the limit. Set to 0 to stop any runs from launching. "
                "Any other negative values are disallowed.",
            ),
            "tag_concurrency_limits": Field(
                config=Noneable(
                    Array(
                        Shape(
                            {
                                "key": String,
                                "value": Field(
                                    ScalarUnion(
                                        scalar_type=String,
                                        non_scalar_schema=Shape({"applyLimitPerUniqueValue": Bool}),
                                    ),
                                    is_required=False,
                                ),
                                "limit": Field(int),
                            }
                        )
                    )
                ),
                is_required=False,
                description="A set of limits that are applied to runs with particular tags. "
                "If a value is set, the limit is applied to only that key-value pair. "
                "If no value is set, the limit is applied across all values of that key. "
                "If the value is set to a dict with `applyLimitPerUniqueValue: true`, the limit "
                "will apply to the number of unique values for that key.",
            ),
            "dequeue_interval_seconds": Field(
                config=IntSource,
                is_required=False,
                description="The interval in seconds at which the Dagster Daemon "
                "should periodically check the run queue for new runs to launch.",
            ),
        }

    @classmethod
    def from_config_value(cls, inst_data, config_value):
        return cls(
            inst_data=inst_data,
            max_concurrent_runs=config_value.get("max_concurrent_runs"),
            tag_concurrency_limits=config_value.get("tag_concurrency_limits"),
            dequeue_interval_seconds=config_value.get("dequeue_interval_seconds"),
        )

    def submit_run(self, context: SubmitRunContext) -> PipelineRun:
        pipeline_run = context.pipeline_run
        check.invariant(pipeline_run.status == PipelineRunStatus.NOT_STARTED)

        enqueued_event = DagsterEvent(
            event_type_value=DagsterEventType.PIPELINE_ENQUEUED.value,
            pipeline_name=pipeline_run.pipeline_name,
        )
        event_record = EventLogEntry(
            user_message="",
            level=logging.INFO,
            pipeline_name=pipeline_run.pipeline_name,
            run_id=pipeline_run.run_id,
            error_info=None,
            timestamp=time.time(),
            dagster_event=enqueued_event,
        )
        self._instance.handle_new_event(event_record)

        run = self._instance.get_run_by_id(pipeline_run.run_id)
        if run is None:
            check.failed(f"Failed to reload run {pipeline_run.run_id}")
        return run

    def cancel_run(self, run_id):
        run = self._instance.get_run_by_id(run_id)
        if not run:
            return False
        # NOTE: possible race condition if the dequeuer acts on this run at the same time
        # https://github.com/dagster-io/dagster/issues/3323
        if run.status == PipelineRunStatus.QUEUED:
            self._instance.report_run_canceling(
                run,
                message="Canceling run from the queue.",
            )
            self._instance.report_run_canceled(run)
            return True
        else:
            return self._instance.run_launcher.terminate(run_id)

import logging
import time
import weakref

from dagster import DagsterEvent, DagsterEventType, DagsterInstance, String, check
from dagster.config import Field
from dagster.config.config_type import Array, Noneable
from dagster.config.field_utils import Shape
from dagster.core.events.log import DagsterEventRecord
from dagster.core.host_representation import ExternalPipeline
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.serdes import ConfigurableClass, ConfigurableClassData

from .base import RunCoordinator


class QueuedRunCoordinator(RunCoordinator, ConfigurableClass):
    """
    Sends runs to the dequeuer process via the run storage. Requires the external process to be
    alive for runs to be launched.
    """

    def __init__(
        self,
        max_concurrent_runs=None,
        tag_concurrency_limits=None,
        dequeue_interval_seconds=None,
        inst_data=None,
    ):
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self._instance_ref = None
        self.max_concurrent_runs = check.opt_int_param(
            max_concurrent_runs, "max_concurrent_runs", 10
        )
        self.tag_concurrency_limits = check.opt_list_param(
            tag_concurrency_limits,
            "tag_concurrency_limits",
        )
        self.dequeue_interval_seconds = check.opt_int_param(
            dequeue_interval_seconds, "dequeue_interval_seconds", 5
        )

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {
            "max_concurrent_runs": Field(config=int, is_required=False),
            "tag_concurrency_limits": Field(
                config=Noneable(
                    Array(
                        Shape(
                            {
                                "key": String,
                                "value": Field(String, is_required=False),
                                "limit": Field(int),
                            }
                        )
                    )
                ),
                is_required=False,
            ),
            "dequeue_interval_seconds": Field(config=int, is_required=False),
        }

    @classmethod
    def from_config_value(cls, inst_data, config_value):
        return cls(
            inst_data=inst_data,
            max_concurrent_runs=config_value.get("max_concurrent_runs"),
            tag_concurrency_limits=config_value.get("tag_concurrency_limits"),
            dequeue_interval_seconds=config_value.get("dequeue_interval_seconds"),
        )

    def initialize(self, instance):
        check.inst_param(instance, "instance", DagsterInstance)
        # Store a weakref to avoid a circular reference / enable GC
        self._instance_ref = weakref.ref(instance)

    @property
    def _instance(self):
        return self._instance_ref() if self._instance_ref else None

    def submit_run(self, pipeline_run, external_pipeline):
        check.inst_param(pipeline_run, "pipeline_run", PipelineRun)
        check.inst_param(external_pipeline, "external_pipeline", ExternalPipeline)
        check.invariant(pipeline_run.status == PipelineRunStatus.NOT_STARTED)

        enqueued_event = DagsterEvent(
            event_type_value=DagsterEventType.PIPELINE_ENQUEUED.value,
            pipeline_name=pipeline_run.pipeline_name,
        )
        event_record = DagsterEventRecord(
            message="",
            user_message="",
            level=logging.INFO,
            pipeline_name=pipeline_run.pipeline_name,
            run_id=pipeline_run.run_id,
            error_info=None,
            timestamp=time.time(),
            dagster_event=enqueued_event,
        )
        self._instance.handle_new_event(event_record)

        return self._instance.get_run_by_id(pipeline_run.run_id)

    def can_cancel_run(self, run_id):
        run = self._instance.get_run_by_id(run_id)
        if not run:
            return False
        if run.status == PipelineRunStatus.QUEUED:
            return True
        else:
            return self._instance.run_launcher.can_terminate(run_id)

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

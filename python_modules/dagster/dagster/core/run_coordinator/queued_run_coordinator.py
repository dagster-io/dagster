import logging
import time
import weakref

from dagster import DagsterEvent, DagsterEventType, DagsterInstance, check
from dagster.core.events.log import DagsterEventRecord
from dagster.core.host_representation import ExternalPipeline
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.serdes import ConfigurableClass, ConfigurableClassData
from dagster.utils.backcompat import experimental

from .base import RunCoordinator


class QueuedRunCoordinator(RunCoordinator, ConfigurableClass):
    """
    Sends runs to the dequeuer process via the run storage. Requires the external process to be
    alive for runs to be launched.
    """

    @experimental
    def __init__(self, inst_data=None):
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self._instance_ref = None

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {}

    @classmethod
    def from_config_value(cls, inst_data, config_value):
        return cls(inst_data=inst_data, **config_value)

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

        return pipeline_run

    def can_cancel_run(self, run_id):
        raise NotImplementedError()

    def cancel_run(self, run_id):
        raise NotImplementedError()

import weakref

from dagster import DagsterInstance, check
from dagster.core.host_representation import ExternalPipeline
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus

from .base import RunsCoordinator


class LaunchImmediateRunsCoordinator(RunsCoordinator):
    """Immediately send runs to the run launcher.
    """

    def __init__(self):
        self._instance_ref = None

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

        return self._instance.launch_run(pipeline_run.run_id, external_pipeline)

    def can_cancel_run(self, run_id):
        raise NotImplementedError()

    def cancel_run(self, run_id):
        raise NotImplementedError()

from dagster import check
from dagster.core.host_representation import ExternalPipeline
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.serdes import ConfigurableClass, ConfigurableClassData

from .base import RunCoordinator


class DefaultRunCoordinator(RunCoordinator, ConfigurableClass):
    """Immediately send runs to the run launcher."""

    def __init__(self, inst_data=None):
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)

        super().__init__()

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {}

    @classmethod
    def from_config_value(cls, inst_data, config_value):
        return cls(inst_data=inst_data, **config_value)

    def submit_run(self, pipeline_run, external_pipeline):
        check.inst_param(pipeline_run, "pipeline_run", PipelineRun)
        check.inst_param(external_pipeline, "external_pipeline", ExternalPipeline)
        check.invariant(pipeline_run.status == PipelineRunStatus.NOT_STARTED)

        return self._instance.launch_run(pipeline_run.run_id, external_pipeline)

    def can_cancel_run(self, run_id):
        return self._instance.run_launcher.can_terminate(run_id)

    def cancel_run(self, run_id):
        return self._instance.run_launcher.terminate(run_id)

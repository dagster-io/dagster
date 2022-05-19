import dagster._check as check
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.serdes import ConfigurableClass, ConfigurableClassData

from .base import RunCoordinator, SubmitRunContext


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

    def submit_run(self, context: SubmitRunContext) -> PipelineRun:
        pipeline_run = context.pipeline_run
        check.invariant(pipeline_run.status == PipelineRunStatus.NOT_STARTED)

        self._instance.launch_run(pipeline_run.run_id, context.workspace)
        run = self._instance.get_run_by_id(pipeline_run.run_id)
        if run is None:
            check.failed(f"Failed to reload run {pipeline_run.run_id}")
        return run

    def cancel_run(self, run_id):
        return self._instance.run_launcher.terminate(run_id)

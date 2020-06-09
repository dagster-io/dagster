from dagster import check
from dagster.core.execution.api import execute_run
from dagster.core.host_representation import ExternalPipeline
from dagster.core.launcher import RunLauncher
from dagster.serdes import ConfigurableClass
from dagster.utils.hosted_user_process import recon_pipeline_from_origin


class SyncInMemoryRunLauncher(RunLauncher, ConfigurableClass):
    def __init__(self, inst_data=None):
        self._inst_data = inst_data
        self._repository = None

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {}

    @staticmethod
    def from_config_value(inst_data, config_value):
        return SyncInMemoryRunLauncher(inst_data=inst_data)

    def launch_run(self, instance, run, external_pipeline):
        check.inst_param(external_pipeline, 'external_pipeline', ExternalPipeline)
        recon_pipeline = recon_pipeline_from_origin(external_pipeline.get_origin())
        execute_run(recon_pipeline, run, instance)
        return run

    def can_terminate(self, run_id):
        return False

    def terminate(self, run_id):
        check.not_implemented('Termination not supported.')

from dagster import check
from dagster.core.execution.api import execute_run
from dagster.core.host_representation import ExternalPipeline
from dagster.core.launcher import RunLauncher
from dagster.serdes import ConfigurableClass


class SyncInMemoryRunLauncher(RunLauncher, ConfigurableClass):
    def __init__(self, hijack_start, inst_data=None):
        self._hijack_start = check.bool_param(hijack_start, 'hijack_start')
        self._inst_data = inst_data
        self._repository = None

    @property
    def inst_data(self):
        return self._inst_data

    @property
    def hijack_start(self):
        return self._hijack_start

    @classmethod
    def config_type(cls):
        return {'hijack_start': bool}

    @staticmethod
    def from_config_value(inst_data, config_value):
        return SyncInMemoryRunLauncher(
            hijack_start=config_value['hijack_start'], inst_data=inst_data
        )

    def launch_run(self, instance, run, external_pipeline=None):
        check.inst_param(external_pipeline, 'external_pipeline', ExternalPipeline)
        pipeline_def = _hosted_user_process_load_pipeline(external_pipeline.handle)
        execute_run(pipeline_def, run, instance)
        return run


# we can do this because we only use in a hosted user process
def _hosted_user_process_load_pipeline(pipeline_handle):
    repo_def = pipeline_handle.repository_handle.environment_handle.in_process_origin.load()
    return repo_def.get_pipeline(pipeline_handle.pipeline_name)

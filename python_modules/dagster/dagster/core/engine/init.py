from collections import namedtuple

from dagster import check
from dagster.core.definitions import ExecutorDefinition, ModeDefinition, PipelineDefinition
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.system_config.objects import EnvironmentConfig


class InitExecutorContext(
    namedtuple(
        'InitExecutorContext',
        'pipeline_def mode_def executor_def pipeline_run environment_config executor_config',
    )
):
    def __new__(
        cls, pipeline_def, mode_def, executor_def, pipeline_run, environment_config, executor_config
    ):
        return super(InitExecutorContext, cls).__new__(
            cls,
            pipeline_def=check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition),
            mode_def=check.inst_param(mode_def, 'mode_def', ModeDefinition),
            executor_def=check.inst_param(executor_def, 'executor_def', ExecutorDefinition),
            pipeline_run=check.inst_param(pipeline_run, 'pipeline_run', PipelineRun),
            environment_config=check.inst_param(
                environment_config, 'environment_config', EnvironmentConfig
            ),
            executor_config=check.dict_param(executor_config, executor_config, key_type=str),
        )

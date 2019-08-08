from collections import namedtuple

from dagster import check
from dagster.core.definitions import ExecutorDefinition, ModeDefinition, PipelineDefinition
from dagster.core.execution.config import RunConfig
from dagster.core.system_config.objects import EnvironmentConfig


class InitExecutorContext(
    namedtuple(
        'InitExecutorContext',
        'pipeline_def mode_def executor_def run_config environment_config executor_config',
    )
):
    def __new__(
        cls, pipeline_def, mode_def, executor_def, run_config, environment_config, executor_config
    ):
        return super(InitExecutorContext, cls).__new__(
            cls,
            pipeline_def=check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition),
            mode_def=check.inst_param(mode_def, 'mode_def', ModeDefinition),
            executor_def=check.inst_param(executor_def, 'executor_def', ExecutorDefinition),
            run_config=check.inst_param(run_config, 'run_config', RunConfig),
            environment_config=check.inst_param(
                environment_config, 'environment_config', EnvironmentConfig
            ),
            executor_config=check.dict_param(executor_config, executor_config, key_type=str),
        )

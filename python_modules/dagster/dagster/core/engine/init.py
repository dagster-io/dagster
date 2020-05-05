from collections import namedtuple

from dagster import check
from dagster.core.definitions import (
    ExecutablePipeline,
    ExecutorDefinition,
    ModeDefinition,
    SystemStorageDefinition,
)
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.system_config.objects import EnvironmentConfig


class InitExecutorContext(
    namedtuple(
        'InitExecutorContext',
        'pipeline mode_def executor_def pipeline_run environment_config '
        'executor_config system_storage_def instance',
    )
):
    '''Executor-specific initialization context.

    Attributes:
        pipeline (ExecutablePipeline): The pipeline to be executed.
        mode_def (ModeDefinition): The mode in which the pipeline is to be executed.
        executor_def (ExecutorDefinition): The definition of the executor currently being
            constructed.
        pipeline_run (PipelineRun): Configuration for this pipeline run.
        environment_config (EnvironmentConfig): The parsed environment configuration for this
            pipeline run.
        executor_config (dict): The parsed config passed to the executor.
        system_storage_def (SystemStorageDefinition): The system storage definition.
        instance (DagsterInstance): The current instance.
    '''

    def __new__(
        cls,
        pipeline,
        mode_def,
        executor_def,
        pipeline_run,
        environment_config,
        executor_config,
        system_storage_def,
        instance,
    ):
        return super(InitExecutorContext, cls).__new__(
            cls,
            pipeline=check.inst_param(pipeline, 'pipeline', ExecutablePipeline),
            mode_def=check.inst_param(mode_def, 'mode_def', ModeDefinition),
            executor_def=check.inst_param(executor_def, 'executor_def', ExecutorDefinition),
            pipeline_run=check.inst_param(pipeline_run, 'pipeline_run', PipelineRun),
            environment_config=check.inst_param(
                environment_config, 'environment_config', EnvironmentConfig
            ),
            executor_config=check.dict_param(executor_config, executor_config, key_type=str),
            system_storage_def=check.inst_param(
                system_storage_def, 'system_storage_def', SystemStorageDefinition
            ),
            instance=check.inst_param(instance, 'instance', DagsterInstance),
        )

    @property
    def pipeline_def(self):
        return self.pipeline.get_definition()

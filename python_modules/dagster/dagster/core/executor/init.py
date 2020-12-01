from collections import namedtuple

from dagster import check
from dagster.core.definitions import (
    ExecutorDefinition,
    IPipeline,
    IntermediateStorageDefinition,
    ModeDefinition,
)
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.system_config.objects import EnvironmentConfig


class InitExecutorContext(
    namedtuple(
        "InitExecutorContext",
        "pipeline mode_def executor_def pipeline_run environment_config "
        "executor_config intermediate_storage_def instance",
    )
):
    """Executor-specific initialization context.

    Attributes:
        pipeline (IPipeline): The pipeline to be executed.
        mode_def (ModeDefinition): The mode in which the pipeline is to be executed.
        executor_def (ExecutorDefinition): The definition of the executor currently being
            constructed.
        pipeline_run (PipelineRun): Configuration for this pipeline run.
        environment_config (EnvironmentConfig): The parsed environment configuration for this
            pipeline run.
        executor_config (dict): The parsed config passed to the executor.
        intermediate_storage_def (Optional[IntermediateStorageDefinition]): The intermediate storage definition.
        instance (DagsterInstance): The current instance.
    """

    def __new__(
        cls,
        pipeline,
        mode_def,
        executor_def,
        pipeline_run,
        environment_config,
        executor_config,
        instance,
        intermediate_storage_def=None,
    ):
        return super(InitExecutorContext, cls).__new__(
            cls,
            pipeline=check.inst_param(pipeline, "pipeline", IPipeline),
            mode_def=check.inst_param(mode_def, "mode_def", ModeDefinition),
            executor_def=check.inst_param(executor_def, "executor_def", ExecutorDefinition),
            pipeline_run=check.inst_param(pipeline_run, "pipeline_run", PipelineRun),
            environment_config=check.inst_param(
                environment_config, "environment_config", EnvironmentConfig
            ),
            executor_config=check.dict_param(executor_config, executor_config, key_type=str),
            intermediate_storage_def=check.opt_inst_param(
                intermediate_storage_def, "intermediate_storage_def", IntermediateStorageDefinition
            ),
            instance=check.inst_param(instance, "instance", DagsterInstance),
        )

    @property
    def pipeline_def(self):
        return self.pipeline.get_definition()

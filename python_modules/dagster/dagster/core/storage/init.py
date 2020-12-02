from collections import namedtuple

from dagster import check
from dagster.core.definitions import (
    IntermediateStorageDefinition,
    ModeDefinition,
    PipelineDefinition,
)
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.storage.type_storage import TypeStoragePluginRegistry
from dagster.core.system_config.objects import EnvironmentConfig


class InitIntermediateStorageContext(
    namedtuple(
        "InitIntermediateStorageContext",
        (
            "pipeline_def mode_def intermediate_storage_def pipeline_run instance environment_config "
            "type_storage_plugin_registry resources intermediate_storage_config"
        ),
    )
):
    """Intermediate storage-specific initialization context.

    Attributes:
        pipeline_def (PipelineDefinition): The definition of the pipeline in context.
        mode_def (ModeDefinition): The definition of the mode in context.
        intermediate_storage_def (IntermediateStorageDefinition): The definition of the intermediate storage to be
            constructed.
        pipeline_run (PipelineRun): The pipeline run in context.
        instance (DagsterInstance): The instance.
        environment_config (EnvironmentConfig): The environment config.
        type_storage_plugin_registry (TypeStoragePluginRegistry): Registry containing custom type
            storage plugins.
        resources (Any): Resources available in context.
        intermediate_storage_config (Dict[str, Any]): The intermediate storage-specific configuration data
            provided by the environment config. The schema for this data is defined by the
            ``config_schema`` argument to :py:class:`IntermediateStorageDefinition`.
    """

    def __new__(
        cls,
        pipeline_def,
        mode_def,
        intermediate_storage_def,
        pipeline_run,
        instance,
        environment_config,
        type_storage_plugin_registry,
        resources,
        intermediate_storage_config,
    ):
        return super(InitIntermediateStorageContext, cls).__new__(
            cls,
            pipeline_def=check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition),
            mode_def=check.inst_param(mode_def, "mode_def", ModeDefinition),
            intermediate_storage_def=check.inst_param(
                intermediate_storage_def, "intermediate_storage_def", IntermediateStorageDefinition
            ),
            pipeline_run=check.inst_param(pipeline_run, "pipeline_run", PipelineRun),
            instance=check.inst_param(instance, "instance", DagsterInstance),
            environment_config=check.inst_param(
                environment_config, "environment_config", EnvironmentConfig
            ),
            type_storage_plugin_registry=check.inst_param(
                type_storage_plugin_registry,
                "type_storage_plugin_registry",
                TypeStoragePluginRegistry,
            ),
            resources=check.not_none_param(resources, "resources"),
            intermediate_storage_config=check.dict_param(
                intermediate_storage_config, intermediate_storage_config, key_type=str
            ),
        )

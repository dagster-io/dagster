from collections import namedtuple

from dagster import check
from dagster.core.definitions import PipelineDefinition, ModeDefinition, SystemStorageDefinition
from dagster.core.definitions.resource import SolidResourcesBuilder
from dagster.core.execution.config import RunConfig
from dagster.core.system_config.objects import EnvironmentConfig
from dagster.core.storage.type_storage import TypeStoragePluginRegistry


class InitSystemStorageContext(
    namedtuple(
        'InitSystemStorageContext',
        (
            'pipeline_def mode_def system_storage_def run_config environment_config '
            'type_storage_plugin_registry solid_resources_builder system_storage_config'
        ),
    )
):
    def __new__(
        cls,
        pipeline_def,
        mode_def,
        system_storage_def,
        run_config,
        environment_config,
        type_storage_plugin_registry,
        solid_resources_builder,
        system_storage_config,
    ):
        return super(InitSystemStorageContext, cls).__new__(
            cls,
            pipeline_def=check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition),
            mode_def=check.inst_param(mode_def, 'mode_def', ModeDefinition),
            system_storage_def=check.inst_param(
                system_storage_def, 'system_storage_def', SystemStorageDefinition
            ),
            run_config=check.inst_param(run_config, 'run_config', RunConfig),
            environment_config=check.inst_param(
                environment_config, 'environment_config', EnvironmentConfig
            ),
            type_storage_plugin_registry=check.inst_param(
                type_storage_plugin_registry,
                'type_storage_plugin_registry',
                TypeStoragePluginRegistry,
            ),
            solid_resources_builder=check.inst_param(
                solid_resources_builder, 'solid_resources_builder', SolidResourcesBuilder
            ),
            system_storage_config=check.dict_param(
                system_storage_config, system_storage_config, key_type=str
            ),
        )

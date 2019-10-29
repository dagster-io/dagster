from collections import namedtuple

from dagster import check
from dagster.core.definitions import ModeDefinition, PipelineDefinition, SystemStorageDefinition
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.storage.type_storage import TypeStoragePluginRegistry
from dagster.core.system_config.objects import EnvironmentConfig


class InitSystemStorageContext(
    namedtuple(
        'InitSystemStorageContext',
        (
            'pipeline_def mode_def system_storage_def pipeline_run instance environment_config '
            'type_storage_plugin_registry resources system_storage_config'
        ),
    )
):
    def __new__(
        cls,
        pipeline_def,
        mode_def,
        system_storage_def,
        pipeline_run,
        instance,
        environment_config,
        type_storage_plugin_registry,
        resources,
        system_storage_config,
    ):
        return super(InitSystemStorageContext, cls).__new__(
            cls,
            pipeline_def=check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition),
            mode_def=check.inst_param(mode_def, 'mode_def', ModeDefinition),
            system_storage_def=check.inst_param(
                system_storage_def, 'system_storage_def', SystemStorageDefinition
            ),
            pipeline_run=check.inst_param(pipeline_run, 'pipeline_run', PipelineRun),
            instance=check.inst_param(instance, 'instance', DagsterInstance),
            environment_config=check.inst_param(
                environment_config, 'environment_config', EnvironmentConfig
            ),
            type_storage_plugin_registry=check.inst_param(
                type_storage_plugin_registry,
                'type_storage_plugin_registry',
                TypeStoragePluginRegistry,
            ),
            resources=check.not_none_param(resources, 'resources'),
            system_storage_config=check.dict_param(
                system_storage_config, system_storage_config, key_type=str
            ),
        )

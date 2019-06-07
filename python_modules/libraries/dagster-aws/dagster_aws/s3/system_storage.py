from dagster import SystemStorageDefinition, SystemStoragePluginData, Dict, Field, String
from dagster.core.definitions.system_storage import mem_system_storage, fs_system_storage
from dagster.core.storage.intermediates_manager import IntermediateStoreIntermediatesManager
from dagster.core.storage.runs import FileSystemRunStorage
from .intermediate_store import S3IntermediateStore


def s3_system_storage_fn(init_context):
    return SystemStoragePluginData(
        run_storage=FileSystemRunStorage(),
        intermediates_manager=IntermediateStoreIntermediatesManager(
            S3IntermediateStore(
                init_context.system_storage_config['s3_bucket'],
                init_context.run_config.run_id,
                init_context.type_storage_plugin_registry,
            )
        ),
    )


def s3_system_storage():
    return SystemStorageDefinition(
        name='s3',
        is_persistent=True,
        system_storage_creation_fn=s3_system_storage_fn,
        config_field=Field(Dict({'s3_bucket': Field(String)})),
    )


def s3_plus_default_storage_defs():
    return [mem_system_storage(), fs_system_storage(), s3_system_storage()]

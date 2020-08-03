from dagster import Field, StringSource, SystemStorageData, intermediate_storage, system_storage
from dagster.core.storage.intermediates_manager import ObjectStoreIntermediateStorage
from dagster.core.storage.system_storage import (
    build_intermediate_storage_from_object_store,
    fs_intermediate_storage,
    fs_system_storage,
    mem_intermediate_storage,
    mem_system_storage,
)

from .file_manager import GCSFileManager
from .intermediate_store import GCSIntermediateStore
from .object_store import GCSObjectStore


@intermediate_storage(
    name='gcs',
    is_persistent=True,
    config_schema={
        'gcs_bucket': Field(StringSource),
        'gcs_prefix': Field(StringSource, is_required=False, default_value='dagster'),
    },
    required_resource_keys={'gcs'},
)
def gcs_intermediate_storage(init_context):
    client = init_context.resources.gcs
    gcs_bucket = init_context.intermediate_storage_config['gcs_bucket']
    gcs_prefix = init_context.intermediate_storage_config['gcs_prefix']
    object_store = GCSObjectStore(gcs_bucket, client=client)

    def root_for_run_id(r_id):
        return object_store.key_for_paths([gcs_prefix, 'storage', r_id])

    return build_intermediate_storage_from_object_store(
        object_store, init_context, root_for_run_id=root_for_run_id
    )


@system_storage(
    name='gcs',
    is_persistent=True,
    config_schema={
        'gcs_bucket': Field(StringSource),
        'gcs_prefix': Field(StringSource, is_required=False, default_value='dagster'),
    },
    required_resource_keys={'gcs'},
)
def gcs_system_storage(init_context):
    client = init_context.resources.gcs
    gcs_key = '{prefix}/storage/{run_id}/files'.format(
        prefix=init_context.system_storage_config['gcs_prefix'],
        run_id=init_context.pipeline_run.run_id,
    )
    return SystemStorageData(
        file_manager=GCSFileManager(
            client=client,
            gcs_bucket=init_context.system_storage_config['gcs_bucket'],
            gcs_base_key=gcs_key,
        ),
        intermediates_manager=ObjectStoreIntermediateStorage(
            GCSIntermediateStore(
                client=client,
                gcs_bucket=init_context.system_storage_config['gcs_bucket'],
                gcs_prefix=init_context.system_storage_config['gcs_prefix'],
                run_id=init_context.pipeline_run.run_id,
                type_storage_plugin_registry=init_context.type_storage_plugin_registry,
            )
        ),
    )


gcs_plus_default_storage_defs = [mem_system_storage, fs_system_storage, gcs_system_storage]
gcs_plus_default_intermediate_storage_defs = [
    mem_intermediate_storage,
    fs_intermediate_storage,
    gcs_intermediate_storage,
]

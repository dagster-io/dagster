from dagster import Field, String, SystemStorageData, system_storage
from dagster.core.storage.intermediates_manager import IntermediateStoreIntermediatesManager
from dagster.core.storage.system_storage import fs_system_storage, mem_system_storage

from .file_manager import GCSFileManager
from .intermediate_store import GCSIntermediateStore


@system_storage(
    name='gcs',
    is_persistent=True,
    config={'gcs_bucket': Field(String)},
    required_resource_keys={'gcs'},
)
def gcs_system_storage(init_context):
    client = init_context.resources.gcs.client
    gcs_key = 'dagster/storage/{run_id}/files'.format(run_id=init_context.pipeline_run.run_id)
    return SystemStorageData(
        file_manager=GCSFileManager(
            client=client,
            gcs_bucket=init_context.system_storage_config['gcs_bucket'],
            gcs_base_key=gcs_key,
        ),
        intermediates_manager=IntermediateStoreIntermediatesManager(
            GCSIntermediateStore(
                client=client,
                gcs_bucket=init_context.system_storage_config['gcs_bucket'],
                run_id=init_context.pipeline_run.run_id,
                type_storage_plugin_registry=init_context.type_storage_plugin_registry,
            )
        ),
    )


gcs_plus_default_storage_defs = [mem_system_storage, fs_system_storage, gcs_system_storage]

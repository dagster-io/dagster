from dagster import system_storage, SystemStorageData, Dict, Field, String
from dagster.core.definitions.system_storage import mem_system_storage, fs_system_storage
from dagster.core.storage.intermediates_manager import IntermediateStoreIntermediatesManager
from dagster.core.storage.runs import FileSystemRunStorage
from .intermediate_store import S3IntermediateStore
from .file_manager import S3FileManager
from .utils import create_s3_session


@system_storage(
    name='s3',
    is_persistent=True,
    config_field=Field(
        Dict({'s3_bucket': Field(String), 's3_key': Field(String, is_optional=True)})
    ),
)
def s3_system_storage(init_context):
    return SystemStorageData(
        file_manager=S3FileManager(
            s3_session=create_s3_session(),
            s3_bucket=init_context.system_storage_config['s3_bucket'],
            s3_base_key=init_context.system_storage_config.get('s3_key', ''),
        ),
        run_storage=FileSystemRunStorage(),
        intermediates_manager=IntermediateStoreIntermediatesManager(
            S3IntermediateStore(
                init_context.system_storage_config['s3_bucket'],
                init_context.run_config.run_id,
                init_context.type_storage_plugin_registry,
            )
        ),
    )


s3_plus_default_storage_defs = [mem_system_storage, fs_system_storage, s3_system_storage]

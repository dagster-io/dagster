from dagster import Field, String
from dagster.core.definitions.system_storage import SystemStorageData, system_storage

from .runs import InMemoryRunStorage, FilesystemRunStorage
from .intermediate_store import FileSystemIntermediateStore
from .intermediates_manager import (
    InMemoryIntermediatesManager,
    IntermediateStoreIntermediatesManager,
)
from .file_manager import LocalFileManager


def create_mem_system_storage_data(init_context):
    return SystemStorageData(
        run_storage=InMemoryRunStorage(),
        intermediates_manager=InMemoryIntermediatesManager(),
        file_manager=LocalFileManager.for_run_id(init_context.run_config.run_id),
    )


@system_storage(name='in_memory', is_persistent=False)
def mem_system_storage(init_context):
    return create_mem_system_storage_data(init_context)


@system_storage(
    name='filesystem', is_persistent=True, config={'base_dir': Field(String, is_optional=True)}
)
def fs_system_storage(init_context):
    base_dir = init_context.system_storage_config.get('base_dir')
    return SystemStorageData(
        file_manager=LocalFileManager.for_run_id(init_context.run_config.run_id),
        run_storage=FilesystemRunStorage(base_dir=base_dir),
        intermediates_manager=IntermediateStoreIntermediatesManager(
            FileSystemIntermediateStore(
                run_id=init_context.run_config.run_id,
                type_storage_plugin_registry=init_context.type_storage_plugin_registry,
                base_dir=base_dir,
            )
        ),
    )


default_system_storage_defs = [mem_system_storage, fs_system_storage]

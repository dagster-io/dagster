from dagster import Field, String
from dagster.core.definitions.system_storage import SystemStorageData, system_storage

from .file_manager import LocalFileManager
from .intermediate_store import FilesystemIntermediateStore
from .intermediates_manager import (
    InMemoryIntermediatesManager,
    IntermediateStoreIntermediatesManager,
)


def create_mem_system_storage_data(init_context):
    return SystemStorageData(
        intermediates_manager=InMemoryIntermediatesManager(),
        file_manager=LocalFileManager.for_instance(
            init_context.instance, init_context.run_config.run_id
        ),
    )


@system_storage(name='in_memory', is_persistent=False)
def mem_system_storage(init_context):
    return create_mem_system_storage_data(init_context)


@system_storage(
    name='filesystem', is_persistent=True, config={'base_dir': Field(String, is_optional=True)}
)
def fs_system_storage(init_context):
    override_dir = init_context.system_storage_config.get('base_dir')
    if override_dir:
        file_manager = LocalFileManager(override_dir)
        intermediate_store = FilesystemIntermediateStore(
            override_dir, init_context.type_storage_plugin_registry
        )
    else:
        file_manager = LocalFileManager.for_instance(
            init_context.instance, init_context.run_config.run_id
        )
        intermediate_store = FilesystemIntermediateStore.for_instance(
            init_context.instance,
            run_id=init_context.run_config.run_id,
            type_storage_plugin_registry=init_context.type_storage_plugin_registry,
        )

    return SystemStorageData(
        file_manager=file_manager,
        intermediates_manager=IntermediateStoreIntermediatesManager(intermediate_store),
    )


default_system_storage_defs = [mem_system_storage, fs_system_storage]

from dagster import check
from dagster.core.storage.intermediate_store import FileSystemIntermediateStore
from dagster.core.storage.intermediates_manager import (
    IntermediatesManager,
    InMemoryIntermediatesManager,
    IntermediateStoreIntermediatesManager,
)
from dagster.core.storage.runs import RunStorage, InMemoryRunStorage, FileSystemRunStorage
from dagster.core.types.field_utils import check_user_facing_opt_field_param
from dagster.core.types import Field, Dict, String


class SystemStorageDefinition:
    '''
    Dagster stores run metadata and intermediate data on the user's behalf.
    The SystemStorageDefinition exists is in order to configure and customized
    those behaviors.

    Example storage definitions are the mem_system_storage in this module,
    which storages all intermediates and run data in memory. and the fs_system_storage,
    which stores all that data in the local filesystem.

    In dagster_aws there is the S3SystemStorageDefinition. We anticipated having
    system storage for every major cloud provider. And it is user customizable
    for users with custom infrastructure needs.

    The storage definitions pass into the ModeDefinition determinees the config
    schema of the "storage" section of the environment configuration.

    Args:
        name (str): Name of the storage mode.
        is_persistent (bool): Does storage def persist in way that can cross process/node
            boundaries. Execution with, for example, the multiprocess executor or within
            the context of dagster-airflow require a persistent storage mode.
        config_field (Field): Configuration field for its section of the storage config.
        system_storage_creation_fn: (Callable[InitSystemStorageContext, SystemStoragePluginData])
            Called by the system. The author of the StorageSystemDefinition must provide this function,
            which consumes the init context and then emits the SystemStoragePluginData.
    '''

    def __init__(self, name, is_persistent, config_field=None, system_storage_creation_fn=None):
        self.name = check.str_param(name, 'name')
        self.is_persistent = check.bool_param(is_persistent, 'is_persistent')
        self.config_field = check_user_facing_opt_field_param(
            config_field,
            'config_field',
            'of a SystemStorageDefinition named {name}'.format(name=name),
        )
        self.system_storage_creation_fn = check.opt_callable_param(
            system_storage_creation_fn, 'system_storage_creation_fn'
        )


class SystemStoragePluginData:
    def __init__(self, run_storage, intermediates_manager):
        self.run_storage = check.inst_param(run_storage, 'run_storage', RunStorage)
        self.intermediates_manager = check.inst_param(
            intermediates_manager, 'intermediates_manager', IntermediatesManager
        )


def mem_system_storage_fn(_init_context):
    return SystemStoragePluginData(
        run_storage=InMemoryRunStorage(), intermediates_manager=InMemoryIntermediatesManager()
    )


def mem_system_storage():
    return SystemStorageDefinition(
        name='in_memory', is_persistent=False, system_storage_creation_fn=mem_system_storage_fn
    )


def fs_system_storage_fn(init_context):
    base_dir = init_context.system_storage_config.get('base_dir')
    return SystemStoragePluginData(
        run_storage=FileSystemRunStorage(base_dir=base_dir),
        intermediates_manager=IntermediateStoreIntermediatesManager(
            FileSystemIntermediateStore(
                run_id=init_context.run_config.run_id,
                types_to_register=init_context.type_storage_plugin_registry,
                base_dir=base_dir,
            )
        ),
    )


def fs_system_storage():
    return SystemStorageDefinition(
        name='filesystem',
        is_persistent=True,
        system_storage_creation_fn=fs_system_storage_fn,
        config_field=Field(Dict({'base_dir': Field(String, is_optional=True)})),
    )

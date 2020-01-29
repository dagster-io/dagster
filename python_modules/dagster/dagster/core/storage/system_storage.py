from dagster.config import Field
from dagster.core.definitions.system_storage import SystemStorageData, system_storage

from .file_manager import LocalFileManager
from .intermediate_store import build_fs_intermediate_store
from .intermediates_manager import (
    InMemoryIntermediatesManager,
    IntermediateStoreIntermediatesManager,
)


def create_mem_system_storage_data(init_context):
    return SystemStorageData(
        intermediates_manager=InMemoryIntermediatesManager(),
        file_manager=LocalFileManager.for_instance(
            init_context.instance, init_context.pipeline_run.run_id
        ),
    )


@system_storage(name='in_memory', is_persistent=False, required_resource_keys=set())
def mem_system_storage(init_context):
    '''The default in-memory system storage.

    In most Dagster environments, this will be the default system storage. It is available by
    default on any :py:class:`ModeDefinition` that does not provide custom system storages. To
    select it explicitly, include the following top-level fragment in config:

    .. code-block:: yaml

        storage:
          in_memory:
    '''
    return create_mem_system_storage_data(init_context)


@system_storage(
    name='filesystem',
    is_persistent=True,
    config={'base_dir': Field(str, is_required=False)},
    required_resource_keys=set(),
)
def fs_system_storage(init_context):
    '''The default filesystem system storage.

    Filesystem system storage is available by default on any :py:class:`ModeDefinition` that does
    not provide custom system storages. To select it, include a fragment such as the following in
    config:

    .. code-block:: yaml

        storage:
          filesystem:
            base_dir: '/path/to/dir/'

    You may omit the ``base_dir`` config value, in which case the filesystem storage will use
    the :py:class:`DagsterInstance`-provided default.
    '''
    override_dir = init_context.system_storage_config.get('base_dir')
    if override_dir:
        file_manager = LocalFileManager(override_dir)
        intermediate_store = build_fs_intermediate_store(
            root_for_run_id=lambda _: override_dir,
            run_id=init_context.pipeline_run.run_id,
            type_storage_plugin_registry=init_context.type_storage_plugin_registry,
        )
    else:
        file_manager = LocalFileManager.for_instance(
            init_context.instance, init_context.pipeline_run.run_id
        )
        intermediate_store = build_fs_intermediate_store(
            init_context.instance.intermediates_directory,
            run_id=init_context.pipeline_run.run_id,
            type_storage_plugin_registry=init_context.type_storage_plugin_registry,
        )

    return SystemStorageData(
        file_manager=file_manager,
        intermediates_manager=IntermediateStoreIntermediatesManager(intermediate_store),
    )


default_system_storage_defs = [mem_system_storage, fs_system_storage]
'''The default 'in_memory' and 'filesystem' system storage definitions.

Framework authors seeking to add their own system storage definitions can extend this list as follows:

.. code-block:: python

    custom_storage_mode = ModeDefinition(
        ...,
        system_storage_defs=default_system_storage_defs + [custom_system_storage_def]
    )
'''

from dagster import check
from dagster.config import Field
from dagster.core.definitions.intermediate_storage import (
    intermediate_storage as intermediate_storage_fn,
)
from dagster.core.definitions.system_storage import SystemStorageData, system_storage
from dagster.core.storage.type_storage import TypeStoragePluginRegistry

from .file_manager import LocalFileManager
from .init import InitIntermediateStorageContext
from .intermediate_storage import (
    ObjectStoreIntermediateStorage,
    build_fs_intermediate_storage,
    build_in_mem_intermediates_storage,
)
from .object_store import FilesystemObjectStore, InMemoryObjectStore, ObjectStore


def create_mem_system_storage_data(init_context):
    return SystemStorageData(
        intermediate_storage=build_in_mem_intermediates_storage(
            init_context.pipeline_run.run_id,
            type_storage_plugin_registry=init_context.type_storage_plugin_registry,
        ),
        file_manager=LocalFileManager.for_instance(
            init_context.instance, init_context.pipeline_run.run_id
        ),
    )


def build_intermediate_storage_from_object_store(
    object_store, init_context, root_for_run_id=lambda _: "",
):
    """constructs an IntermediateStorage object from an object store and an init_context
        Call from within an intermediate_storage_definition
        Args:
            object_store(ObjectStore): The object store on which to base the intermediate store.
            init_context(InitIntermediateStorageContext):  the context from which to create the intermediates manager
            root_for_run_id_creator(Callable[[str], str]):
                        a function that converts from your run ID to the root of your object storage paths
        """
    object_store = check.inst_param(object_store, "object_store", ObjectStore)
    root_for_run_id = check.callable_param(root_for_run_id, "root_for_run_id")
    init_context = check.inst_param(init_context, "init_context", InitIntermediateStorageContext)

    return ObjectStoreIntermediateStorage(
        object_store=object_store,
        run_id=init_context.pipeline_run.run_id,
        root_for_run_id=root_for_run_id,
        type_storage_plugin_registry=init_context.type_storage_plugin_registry
        if init_context.type_storage_plugin_registry
        else TypeStoragePluginRegistry(types_to_register=[]),
    )


@system_storage(name="in_memory", is_persistent=False, required_resource_keys=set())
def mem_system_storage(init_context):
    """The default in-memory system storage.

    In most Dagster environments, this will be the default system storage. It is available by
    default on any :py:class:`ModeDefinition` that does not provide custom system storages. To
    select it explicitly, include the following top-level fragment in config:

    .. code-block:: yaml

        storage:
          in_memory:
    """
    return create_mem_system_storage_data(init_context)


@intermediate_storage_fn(name="in_memory", is_persistent=False, required_resource_keys=set())
def mem_intermediate_storage(init_context):
    """The default in-memory intermediate storage.

    In-memory intermediate storage is the default on any pipeline run that does
    not configure any custom intermediate storage.

    Keep in mind when using this storage that intermediates will not be persisted after the pipeline
    run ends. Use a persistent intermediate storage like :py:func:`fs_intermediate_storage` to
    persist intermediates and take advantage of advanced features like pipeline re-execution.
    """
    object_store = InMemoryObjectStore()
    return build_intermediate_storage_from_object_store(
        object_store=object_store, init_context=init_context
    )


@system_storage(
    name="filesystem",
    is_persistent=True,
    config_schema={"base_dir": Field(str, is_required=False)},
    required_resource_keys=set(),
)
def fs_system_storage(init_context):
    """The default filesystem system storage.

    Filesystem system storage is available by default on any :py:class:`ModeDefinition` that does
    not provide custom system storages. To select it, include a fragment such as the following in
    config:

    .. code-block:: yaml

        storage:
          filesystem:
            base_dir: '/path/to/dir/'

    You may omit the ``base_dir`` config value, in which case the filesystem storage will use
    the :py:class:`DagsterInstance`-provided default.
    """
    override_dir = init_context.system_storage_config.get("base_dir")
    if override_dir:
        file_manager = LocalFileManager(override_dir)
        intermediate_storage = build_fs_intermediate_storage(
            root_for_run_id=lambda _: override_dir,
            run_id=init_context.pipeline_run.run_id,
            type_storage_plugin_registry=init_context.type_storage_plugin_registry,
        )
    else:
        file_manager = LocalFileManager.for_instance(
            init_context.instance, init_context.pipeline_run.run_id
        )
        intermediate_storage = build_fs_intermediate_storage(
            init_context.instance.intermediates_directory,
            run_id=init_context.pipeline_run.run_id,
            type_storage_plugin_registry=init_context.type_storage_plugin_registry,
        )

    return SystemStorageData(file_manager=file_manager, intermediate_storage=intermediate_storage,)


@intermediate_storage_fn(
    name="filesystem",
    is_persistent=True,
    config_schema={"base_dir": Field(str, is_required=False)},
    required_resource_keys=set(),
)
def fs_intermediate_storage(init_context):
    """The default filesystem intermediate storage.

    Filesystem system storage is available by default on any :py:class:`ModeDefinition` that does
    not provide custom system storages. To select it, include a fragment such as the following in
    config:

    .. code-block:: yaml

        intermediate_storage:
          filesystem:
            base_dir: '/path/to/dir/'

    You may omit the ``base_dir`` config value, in which case the filesystem storage will use
    the :py:class:`DagsterInstance`-provided default.
    """
    object_store = FilesystemObjectStore()
    override_dir = init_context.intermediate_storage_config.get("base_dir")
    if override_dir:
        root_for_run_id = lambda _: override_dir
    else:
        root_for_run_id = init_context.instance.intermediates_directory

    return build_intermediate_storage_from_object_store(
        object_store, init_context, root_for_run_id=root_for_run_id
    )


default_system_storage_defs = [mem_system_storage, fs_system_storage]

"""The default 'in_memory' and 'filesystem' system storage definitions.

Framework authors seeking to add their own system storage definitions can extend this list as follows:

.. code-block:: python

    custom_storage_mode = ModeDefinition(
        ...,
        system_storage_defs=default_system_storage_defs + [custom_system_storage_def]
    )
"""

default_intermediate_storage_defs = [mem_intermediate_storage, fs_intermediate_storage]
"""The default 'in_memory' and 'filesystem' intermediate storage definitions.

Framework authors seeking to add their own intermediate storage definitions can extend this list as follows:

.. code-block:: python

    custom_storage_mode = ModeDefinition(
        ...,
        intermediate_storage_defs=default_intermediate_storage_defs + [custom_intermediate_storage_def]
    )
"""

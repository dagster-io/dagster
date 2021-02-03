from dagster import check
from dagster.config import Field
from dagster.core.definitions.intermediate_storage import IntermediateStorageDefinition
from dagster.core.definitions.intermediate_storage import (
    intermediate_storage as intermediate_storage_fn,
)
from dagster.core.storage.io_manager import io_manager
from dagster.core.storage.type_storage import (
    TypeStoragePluginRegistry,
    construct_type_storage_plugin_registry,
)
from dagster.core.system_config.objects import EnvironmentConfig

from .init import InitIntermediateStorageContext
from .intermediate_storage import IntermediateStorageAdapter, ObjectStoreIntermediateStorage
from .object_store import FilesystemObjectStore, InMemoryObjectStore, ObjectStore


def build_intermediate_storage_from_object_store(
    object_store,
    init_context,
    root_for_run_id=lambda _: "",
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


default_intermediate_storage_defs = [mem_intermediate_storage, fs_intermediate_storage]
"""The default 'in_memory' and 'filesystem' intermediate storage definitions.

Framework authors seeking to add their own intermediate storage definitions can extend this list as follows:

.. code-block:: python

    custom_storage_mode = ModeDefinition(
        ...,
        intermediate_storage_defs=default_intermediate_storage_defs + [custom_intermediate_storage_def]
    )
"""


def io_manager_from_intermediate_storage(intermediate_storage_def):
    """Define an :py:class:`IOManagerDefinition` from an existing :py:class:`IntermediateStorageDefinition`.

    This method is used to adapt an existing user-defined intermediate storage to a IO manager
    resource, for example:

    .. code-block:: python

        my_io_manager_def = io_manager_from_intermediate_storage(my_intermediate_storage_def)

        @pipeline(mode_defs=[ModeDefinition(resource_defs={"io_manager": my_io_manager_def})])
        def my_pipeline():
            ...


    Args:
        intermediate_storage_def (IntermediateStorageDefinition): The intermediate storage definition
            to be converted to an IO manager definition.

    Returns:
        IOManagerDefinition
    """

    check.inst_param(
        intermediate_storage_def, "intermediate_storage_def", IntermediateStorageDefinition
    )

    @io_manager
    def _io_manager(init_context):
        pipeline_run = init_context.pipeline_run
        instance = init_context.instance_for_backwards_compat
        pipeline_def = init_context.pipeline_def_for_backwards_compat
        # depend on InitResourceContext.instance_for_backwards_compat and pipeline_def_for_backwards_compat
        environment_config = EnvironmentConfig.build(
            pipeline_def, pipeline_run.run_config, mode=pipeline_run.mode
        )
        mode_def = pipeline_def.get_mode_definition(pipeline_run.mode)

        intermediate_storage_context = InitIntermediateStorageContext(
            pipeline_def=pipeline_def,
            mode_def=mode_def,
            intermediate_storage_def=intermediate_storage_def,
            pipeline_run=pipeline_run,
            instance=instance,
            environment_config=environment_config,
            type_storage_plugin_registry=construct_type_storage_plugin_registry(
                pipeline_def, intermediate_storage_def
            ),
            resources=init_context.resources,
            intermediate_storage_config=environment_config.intermediate_storage.intermediate_storage_config,
        )

        intermediate_storage = intermediate_storage_def.intermediate_storage_creation_fn(
            intermediate_storage_context
        )

        return IntermediateStorageAdapter(intermediate_storage)

    return _io_manager

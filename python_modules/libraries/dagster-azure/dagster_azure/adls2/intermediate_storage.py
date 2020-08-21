from dagster import check
from dagster.core.storage.intermediate_storage import ObjectStoreIntermediateStorage
from dagster.core.storage.type_storage import TypeStoragePluginRegistry

from .object_store import ADLS2ObjectStore


class ADLS2IntermediateStorage(ObjectStoreIntermediateStorage):
    """Intermediate store using Azure Data Lake Storage Gen2.

    This intermediate store uses ADLS2 APIs to communicate with the storage,
    which are better optimised for various tasks than regular Blob storage.
    """

    def __init__(
        self,
        file_system,
        run_id,
        adls2_client,
        blob_client,
        type_storage_plugin_registry=None,
        prefix="dagster",
    ):
        check.str_param(file_system, "file_system")
        check.str_param(prefix, "prefix")
        check.str_param(run_id, "run_id")

        object_store = ADLS2ObjectStore(file_system, adls2_client, blob_client)

        def root_for_run_id(r_id):
            return object_store.key_for_paths([prefix, "storage", r_id])

        super(ADLS2IntermediateStorage, self).__init__(
            object_store,
            root_for_run_id=root_for_run_id,
            run_id=run_id,
            type_storage_plugin_registry=check.inst_param(
                type_storage_plugin_registry
                if type_storage_plugin_registry
                else TypeStoragePluginRegistry(types_to_register=[]),
                "type_storage_plugin_registry",
                TypeStoragePluginRegistry,
            ),
        )

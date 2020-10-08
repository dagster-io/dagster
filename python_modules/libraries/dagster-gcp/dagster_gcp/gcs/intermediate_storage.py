from dagster import check
from dagster.core.storage.intermediate_storage import ObjectStoreIntermediateStorage
from dagster.core.storage.type_storage import TypeStoragePluginRegistry

from .object_store import GCSObjectStore


class GCSIntermediateStorage(ObjectStoreIntermediateStorage):
    def __init__(
        self,
        gcs_bucket,
        run_id,
        client=None,
        type_storage_plugin_registry=None,
        gcs_prefix="dagster",
    ):
        check.str_param(gcs_bucket, "gcs_bucket")
        check.str_param(gcs_prefix, "gcs_prefix")
        check.str_param(run_id, "run_id")

        object_store = GCSObjectStore(gcs_bucket, client=client)

        def root_for_run_id(r_id):
            return object_store.key_for_paths([gcs_prefix, "storage", r_id])

        super(GCSIntermediateStorage, self).__init__(
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

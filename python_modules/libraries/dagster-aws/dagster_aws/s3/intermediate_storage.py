from dagster import check
from dagster.core.storage.intermediate_storage import ObjectStoreIntermediateStorage
from dagster.core.storage.type_storage import TypeStoragePluginRegistry

from .object_store import S3ObjectStore


class S3IntermediateStorage(ObjectStoreIntermediateStorage):
    def __init__(
        self,
        s3_bucket,
        run_id,
        s3_session=None,
        type_storage_plugin_registry=None,
        s3_prefix="dagster",
    ):
        check.str_param(s3_bucket, "s3_bucket")
        check.str_param(s3_prefix, "s3_prefix")
        check.str_param(run_id, "run_id")

        object_store = S3ObjectStore(s3_bucket, s3_session=s3_session)

        def root_for_run_id(r_id):
            return object_store.key_for_paths([s3_prefix, "storage", r_id])

        super(S3IntermediateStorage, self).__init__(
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

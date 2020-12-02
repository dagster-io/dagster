from dagster import Field, StringSource, intermediate_storage
from dagster.core.storage.system_storage import (
    build_intermediate_storage_from_object_store,
    fs_intermediate_storage,
    mem_intermediate_storage,
)

from .object_store import GCSObjectStore


@intermediate_storage(
    name="gcs",
    is_persistent=True,
    config_schema={
        "gcs_bucket": Field(StringSource),
        "gcs_prefix": Field(StringSource, is_required=False, default_value="dagster"),
    },
    required_resource_keys={"gcs"},
)
def gcs_intermediate_storage(init_context):
    client = init_context.resources.gcs
    gcs_bucket = init_context.intermediate_storage_config["gcs_bucket"]
    gcs_prefix = init_context.intermediate_storage_config["gcs_prefix"]
    object_store = GCSObjectStore(gcs_bucket, client=client)

    def root_for_run_id(r_id):
        return object_store.key_for_paths([gcs_prefix, "storage", r_id])

    return build_intermediate_storage_from_object_store(
        object_store, init_context, root_for_run_id=root_for_run_id
    )


gcs_plus_default_intermediate_storage_defs = [
    mem_intermediate_storage,
    fs_intermediate_storage,
    gcs_intermediate_storage,
]

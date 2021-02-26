from dagster import Field, StringSource, intermediate_storage
from dagster.core.storage.system_storage import (
    build_intermediate_storage_from_object_store,
    fs_intermediate_storage,
    mem_intermediate_storage,
)

from .object_store import ADLS2ObjectStore


@intermediate_storage(
    name="adls2",
    is_persistent=True,
    config_schema={
        "adls2_file_system": Field(StringSource, description="ADLS Gen2 file system name"),
        "adls2_prefix": Field(StringSource, is_required=False, default_value="dagster"),
    },
    required_resource_keys={"adls2"},
)
def adls2_intermediate_storage(init_context):
    """Persistent intermediate storage using Azure Data Lake Storage Gen2 for storage.

    Suitable for intermediates storage for distributed executors, so long as
    each execution node has network connectivity and credentials for ADLS and
    the backing container.

    Attach this intermediate storage definition, as well as the :py:data:`~dagster_azure.adls2_resource`
    it requires, to a :py:class:`~dagster.ModeDefinition` in order to make it available to your
    pipeline:

    .. code-block:: python

        pipeline_def = PipelineDefinition(
            mode_defs=[
                ModeDefinition(
                    resource_defs={'adls2': adls2_resource, ...},
                    intermediate_storage_defs=[adls2_intermediate_storage],
                    ...
                ), ...
            ], ...
        )

    You may configure this storage as follows:

    .. code-block:: YAML

        intermediate_storage:
          adls2:
            config:
              adls2_sa: my-best-storage-account
              adls2_file_system: my-cool-file-system
              adls2_prefix: good/prefix-for-files-
    """
    resource = init_context.resources.adls2
    file_system = init_context.intermediate_storage_config["adls2_file_system"]
    adls2_client = resource.adls2_client
    blob_client = resource.blob_client
    prefix = init_context.intermediate_storage_config["adls2_prefix"]
    object_store = ADLS2ObjectStore(file_system, adls2_client, blob_client)

    def root_for_run_id(r_id):
        return object_store.key_for_paths([prefix, "storage", r_id])

    return build_intermediate_storage_from_object_store(
        object_store=object_store, init_context=init_context, root_for_run_id=root_for_run_id
    )


adls2_plus_default_intermediate_storage_defs = [
    mem_intermediate_storage,
    fs_intermediate_storage,
    adls2_intermediate_storage,
]

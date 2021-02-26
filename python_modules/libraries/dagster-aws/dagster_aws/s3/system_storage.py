from dagster import Field, StringSource, intermediate_storage
from dagster.core.storage.system_storage import (
    build_intermediate_storage_from_object_store,
    fs_intermediate_storage,
    mem_intermediate_storage,
)

from .object_store import S3ObjectStore


@intermediate_storage(
    name="s3",
    is_persistent=True,
    config_schema={
        "s3_bucket": Field(StringSource),
        "s3_prefix": Field(StringSource, is_required=False, default_value="dagster"),
    },
    required_resource_keys={"s3"},
)
def s3_intermediate_storage(init_context):
    """Persistent intermediate storage using S3 for storage.

    Suitable for intermediates storage for distributed executors, so long as
    each execution node has network connectivity and credentials for S3 and
    the backing bucket.

    Attach this storage definition, as well as the :py:data:`~dagster_aws.s3_resource` it
    requires, to a :py:class:`~dagster.ModeDefinition` in order to make it available to your
    pipeline:

    .. code-block:: python

        pipeline_def = PipelineDefinition(
            mode_defs=[
                ModeDefinition(
                    resource_defs={'s3': s3_resource, ...},
                    intermediate_storage_defs=[s3_intermediate_storage],
                    ...
                ), ...
            ], ...
        )

    You may configure this storage as follows:

    .. code-block:: YAML

        intermediate_storage:
          s3:
            config:
              s3_bucket: my-cool-bucket
              s3_prefix: good/prefix-for-files-
    """
    s3_session = init_context.resources.s3
    s3_bucket = init_context.intermediate_storage_config["s3_bucket"]
    object_store = S3ObjectStore(s3_bucket, s3_session=s3_session)
    s3_prefix = init_context.intermediate_storage_config["s3_prefix"]

    def root_for_run_id(r_id):
        return object_store.key_for_paths([s3_prefix, "storage", r_id])

    return build_intermediate_storage_from_object_store(
        object_store, init_context=init_context, root_for_run_id=root_for_run_id
    )


s3_plus_default_intermediate_storage_defs = [
    mem_intermediate_storage,
    fs_intermediate_storage,
    s3_intermediate_storage,
]

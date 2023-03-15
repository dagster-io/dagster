from dagster import build_init_resource_context, io_manager
from dagster_aws.s3 import s3_pickle_io_manager


@io_manager(required_resource_keys={"s3_bucket", "s3"})
def common_bucket_s3_pickle_io_manager(init_context):
    """A version of the s3_pickle_io_manager that gets its bucket from another resource."""
    return s3_pickle_io_manager(
        build_init_resource_context(
            config={"s3_bucket": init_context.resources.s3_bucket},
            resources={"s3": init_context.resources.s3},
        )
    )

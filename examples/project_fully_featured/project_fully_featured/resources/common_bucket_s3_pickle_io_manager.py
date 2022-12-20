from dagster_aws.s3 import
from dagster_aws.s3.io_manager import PickledObjectS3IOManager
from dagster import io_manager


@io_manager(required_resource_keys={"s3_bucket", "s3"})
def common_bucket_s3_pickle_io_manager(init_context):
    """
    A version of the s3_pickle_io_manager that gets its bucket from another resource.
    """
    return PickledObjectS3IOManager(
        s3_bucket=init_context.resources.s3_bucket, s3_session=init_context.resources.s3
    )

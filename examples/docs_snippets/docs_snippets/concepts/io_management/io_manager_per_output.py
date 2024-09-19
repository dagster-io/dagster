# start_marker
from dagster_aws.s3 import S3PickleIOManager, S3Resource

from dagster import FilesystemIOManager, Out, job, op


@op(out=Out(io_manager_key="fs"))
def op_1():
    return 1


@op(out=Out(io_manager_key="s3_io"))
def op_2(a):
    return a + 1


@job(
    resource_defs={
        "fs": FilesystemIOManager(),
        "s3_io": S3PickleIOManager(s3_resource=S3Resource(), s3_bucket="test-bucket"),
    }
)
def my_job():
    op_2(op_1())


# end_marker

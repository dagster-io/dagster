# start_marker
from dagster_aws.s3 import s3_pickle_io_manager, s3_resource

from dagster import Out, fs_io_manager, job, op


@op(out=Out(io_manager_key="fs"))
def op_1():
    return 1


@op(out=Out(io_manager_key="s3_io"))
def op_2(a):
    return a + 1


@job(
    resource_defs={
        "fs": fs_io_manager,
        "s3_io": s3_pickle_io_manager,
        "s3": s3_resource,
    }
)
def my_job():
    op_2(op_1())


# end_marker

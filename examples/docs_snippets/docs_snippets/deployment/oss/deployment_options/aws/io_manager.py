from dagster_aws.s3.io_manager import s3_pickle_io_manager
from dagster_aws.s3.resources import s3_resource

import dagster as dg


@dg.op(out=dg.Out(dg.Int))
def my_op():
    return 1


@dg.job(
    resource_defs={
        "io_manager": s3_pickle_io_manager,
        "s3": s3_resource,
    }
)
def my_job():
    my_op()

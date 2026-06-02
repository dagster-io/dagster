# start_local_job_marker

from dagster_dask import dask_executor

import dagster as dg


@dg.op
def hello_world():
    return "Hello, World!"


@dg.job(executor_def=dask_executor)
def local_dask_job():
    hello_world()


# end_local_job_marker

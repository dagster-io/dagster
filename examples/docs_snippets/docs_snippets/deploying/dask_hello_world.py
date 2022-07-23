# start_local_job_marker

from dagster_dask import dask_executor

from dagster import job, op


@op
def hello_world():
    return "Hello, World!"


@job(executor_def=dask_executor)
def local_dask_job():
    hello_world()


# end_local_job_marker

# isort: skip_file
# pylint: disable=reimported
# start_executor_on_job
from dagster import multiprocess_executor, job, graph

# Providing an executor using the job decorator
@job(executor_def=multiprocess_executor)
def the_job():
    ...


@graph
def the_graph():
    ...


# Providing an executor using graph_def.to_job(...)
other_job = the_graph.to_job(executor_def=multiprocess_executor)


# end_executor_on_job

# start_executor_on_repo
from dagster import multiprocess_executor, define_asset_job, asset, repository


@asset
def the_asset():
    pass


asset_job = define_asset_job("the_job", selection="*")


@job
def op_job():
    ...


# op_job and asset_job will both use the default_executor_def,
# since neither define their own executor.
@repository(default_executor_def=multiprocess_executor)
def the_repo():
    return [the_asset, asset_job, op_job]


# end_executor_on_repo

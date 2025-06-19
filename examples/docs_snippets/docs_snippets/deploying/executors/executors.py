# ruff: isort: skip_file

# start_executor_on_job
import dagster as dg


# Providing an executor using the job decorator
@dg.job(executor_def=dg.multiprocess_executor)
def the_job(): ...


@dg.graph
def the_graph(): ...


# Providing an executor using graph_def.to_job(...)
other_job = the_graph.to_job(executor_def=dg.multiprocess_executor)


# end_executor_on_job

# start_executor_on_repo
import dagster as dg


@dg.asset
def the_asset():
    pass


asset_job = dg.define_asset_job("the_job", selection="*")


@dg.job
def op_job(): ...


# op_job and asset_job will both use the multiprocess_executor,
# since neither define their own executor.

defs = dg.Definitions(
    assets=[the_asset], jobs=[asset_job, op_job], executor=dg.multiprocess_executor
)

# end_executor_on_repo

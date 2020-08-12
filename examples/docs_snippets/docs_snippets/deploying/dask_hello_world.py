from dagster_dask import dask_executor

from dagster import ModeDefinition, default_executors, pipeline, solid


@solid
def hello_world(_):
    return "Hello, World!"


@pipeline(mode_defs=[ModeDefinition(executor_defs=default_executors + [dask_executor])])
def dask_pipeline():
    return hello_world()

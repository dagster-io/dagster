from dagster_pandas.examples import papermill_pandas_hello_world_pipeline
from dagster_pandas.examples.pandas_hello_world.pipeline import pandas_hello_world

from dagster import repository


@repository
def pandas_hello_world_repo():
    return [pandas_hello_world, papermill_pandas_hello_world_pipeline]

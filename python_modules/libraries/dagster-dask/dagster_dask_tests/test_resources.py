import pytest
from dagster_dask import DataFrame, dask_resource


@solid(
    input_defs=[InputDefinition(dagster_type=DataFrame, name="df")],
    output_defs=[OutputDefinition(dagster_type=DataFrame, name="df")],
    required_resource_keys={"dask"},
)
def passthrough(_, df):
    return df

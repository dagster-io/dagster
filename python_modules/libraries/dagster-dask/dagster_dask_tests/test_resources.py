from dagster import (
    DagsterInstance,
    Dict,
    InputDefinition,
    ModeDefinition,
    Output,
    OutputDefinition,
    ResourceDefinition,
    execute_pipeline,
    file_relative_path,
    pipeline,
    solid,
)
import dask.dataframe as dd
from dask.dataframe.utils import assert_eq

from dagster_dask import DataFrame, dask_resource


@solid(
    output_defs=[
        OutputDefinition(dagster_type=Dict, name="scheduler_info"),
        OutputDefinition(dagster_type=Dict, name="nthreads"),
    ],
    required_resource_keys={"dask"},
)
def scheduler_info_solid(context):
    client = context.resources.dask.client

    yield Output(client.scheduler_info(), "scheduler_info")
    yield Output(client.nthreads(), "nthreads")


@pipeline(
    mode_defs=[
        ModeDefinition(resource_defs={"dask": dask_resource})
    ]
)
def scheduler_info_pipeline():
    return scheduler_info_solid()


def test_custom_local_cluster():
    cluster_config = {
        "n_workers": 2,
        "threads_per_worker": 3,
        "dashboard_address": None,
    }

    run_config = {"resources": {"dask": {"config": {"cluster": {"local": cluster_config}}}}}
    result = execute_pipeline(scheduler_info_pipeline, run_config=run_config, instance=DagsterInstance.local_temp())

    scheduler_info = result.result_for_solid("scheduler_info_solid").output_value("scheduler_info")
    assert len(scheduler_info["workers"]) == cluster_config["n_workers"]

    nthreads = result.result_for_solid("scheduler_info_solid").output_value("nthreads")
    assert all(v == cluster_config["threads_per_worker"] for v in nthreads.values())

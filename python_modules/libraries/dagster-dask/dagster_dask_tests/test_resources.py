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


@pipeline(mode_defs=[ModeDefinition(resource_defs={"dask": dask_resource})])
def scheduler_info_pipeline():
    return scheduler_info_solid()


def test_single_local_cluster():
    cluster_config = {
        "n_workers": 2,
        "threads_per_worker": 1,
        "dashboard_address": None,
    }

    run_config = {
        "resources": {"dask": {"config": {"cluster": {"local": cluster_config}}}}
    }
    result = execute_pipeline(
        scheduler_info_pipeline,
        run_config=run_config,
        instance=DagsterInstance.local_temp(),
    )
    _assert_scheduler_info_result(result, cluster_config)


def test_multiple_local_cluster():
    cluster_configs = [
        {
            "n_workers": 1,
            "threads_per_worker": 2,
            "dashboard_address": None,
        },
        {
            "n_workers": 2,
            "threads_per_worker": 1,
            "dashboard_address": None,
        },
    ]

    for cluster_config in cluster_configs:
        run_config = {
            "resources": {"dask": {"config": {"cluster": {"local": cluster_config}}}}
        }
        result = execute_pipeline(
            scheduler_info_pipeline,
            run_config=run_config,
            instance=DagsterInstance.local_temp(),
        )
        _assert_scheduler_info_result(result, cluster_config)


def _assert_scheduler_info_result(result, config):
    scheduler_info = result.result_for_solid("scheduler_info_solid").output_value(
        "scheduler_info"
    )
    assert len(scheduler_info["workers"]) == config["n_workers"]

    nthreads = result.result_for_solid("scheduler_info_solid").output_value("nthreads")
    assert all(v == config["threads_per_worker"] for v in nthreads.values())

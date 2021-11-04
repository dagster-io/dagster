from dagster import (
    Dict,
    ModeDefinition,
    Output,
    OutputDefinition,
    execute_pipeline,
    pipeline,
    solid,
)
from dagster.core.test_utils import instance_for_test
from dagster_dask import dask_resource
from dask.distributed import Client


@solid(
    output_defs=[
        OutputDefinition(dagster_type=Dict, name="scheduler_info"),
        OutputDefinition(dagster_type=Dict, name="nthreads"),
    ],
    required_resource_keys={"dask"},
)
def scheduler_info_solid(context):
    with context.resources.dask.client.as_current():
        client = Client.current()

        yield Output(client.scheduler_info(), "scheduler_info")
        yield Output(client.nthreads(), "nthreads")


@pipeline(mode_defs=[ModeDefinition(resource_defs={"dask": dask_resource})])
def scheduler_info_pipeline():
    scheduler_info_solid()


def test_single_local_cluster():
    cluster_config = {
        "n_workers": 2,
        "threads_per_worker": 1,
        "dashboard_address": None,
    }
    with instance_for_test() as instance:
        run_config = {"resources": {"dask": {"config": {"cluster": {"local": cluster_config}}}}}
        result = execute_pipeline(
            scheduler_info_pipeline, run_config=run_config, instance=instance,
        )
        _assert_scheduler_info_result(result, cluster_config)


def test_multiple_local_cluster():
    cluster_configs = [
        {"n_workers": 1, "threads_per_worker": 2, "dashboard_address": None,},
        {"n_workers": 2, "threads_per_worker": 1, "dashboard_address": None,},
    ]

    with instance_for_test() as instance:
        for cluster_config in cluster_configs:
            run_config = {"resources": {"dask": {"config": {"cluster": {"local": cluster_config}}}}}
            result = execute_pipeline(
                scheduler_info_pipeline, run_config=run_config, instance=instance,
            )
            _assert_scheduler_info_result(result, cluster_config)


def _assert_scheduler_info_result(result, config):
    scheduler_info_solid_result = result.result_for_solid("scheduler_info_solid")

    scheduler_info = scheduler_info_solid_result.output_value("scheduler_info")
    assert len(scheduler_info["workers"]) == config["n_workers"]

    nthreads = scheduler_info_solid_result.output_value("nthreads")
    assert all(v == config["threads_per_worker"] for v in nthreads.values())

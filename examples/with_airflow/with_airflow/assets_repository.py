import os

from dagster import AssetKey, asset, repository

# start_repo_marker_0
from dagster_airflow import load_assets_from_airflow_dag

from with_airflow.airflow_simple_dag import simple_dag


@asset(group_name="simple_dag")
def new_upstream_asset_1():
    return 1


@asset(group_name="simple_dag")
def new_upstream_asset_2():
    return 2


simple_asset = load_assets_from_airflow_dag(
    simple_dag,
    task_ids_by_asset_key={
        AssetKey("task_instances_0"): {
            "get_task_instance_0",
            "get_task_instance_0_0",
            "get_task_instance_0_1",
            "get_task_instance_0_2",
        },
        AssetKey("task_instance_2"): {"get_task_instance_2"},
        AssetKey("new_asset"): {"sink_task_bar", "sink_task_foo"},
        AssetKey("task_instances_1"): {"get_task_instance_1"},
        AssetKey("task_instances_1_0"): {"get_task_instance_1_0"},
        AssetKey("task_instances_1_1"): {"get_task_instance_1_1"},
        AssetKey("task_instances_1_2"): {"get_task_instance_1_2"},
    },
    upstream_asset_keys_by_task_id={
        "sink_task_bar": {AssetKey("new_upstream_asset_1"), AssetKey("new_upstream_asset_2")},
        "get_task_instance_1_2": {AssetKey("new_upstream_asset_2")},
        "get_task_instance_2_2": {AssetKey("new_upstream_asset_2")},
    },
)


@repository
def sda_examples():
    return [simple_asset, new_upstream_asset_1, new_upstream_asset_2]

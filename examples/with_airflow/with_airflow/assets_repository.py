from dagster import AssetKey, Definitions, asset
from dagster_airflow import load_assets_from_airflow_dag, make_ephemeral_airflow_db_resource

from with_airflow.airflow_simple_dag import simple_dag


@asset(group_name="simple_dag")
def new_upstream_asset_1():
    return 1


@asset(group_name="simple_dag")
def new_upstream_asset_2():
    return 2


simple_assets = load_assets_from_airflow_dag(
    simple_dag,
    task_ids_by_asset_key={
        AssetKey("task_instances_0"): {"get_task_instance_0"},
        AssetKey("task_instance_2"): {"get_task_instance_2"},
        AssetKey("new_asset"): {"sink_task_bar"},
        AssetKey("task_instances_1"): {"get_task_instance_1"},
        AssetKey("task_instances_1_0"): {"get_task_instance_1_0"},
        AssetKey("task_instances_1_1"): {"get_task_instance_1_1"},
        AssetKey("task_instances_1_2"): {"get_task_instance_1_2"},
    },
    upstream_dependencies_by_asset_key={
        AssetKey("new_asset"): {AssetKey("new_upstream_asset_1"), AssetKey("new_upstream_asset_2")},
        AssetKey("task_instances_1_2"): {AssetKey("new_upstream_asset_2")},
        AssetKey("task_instances_1"): {AssetKey("new_upstream_asset_2")},
    },
)


sda_examples = Definitions(
    assets=[*simple_assets, new_upstream_asset_1, new_upstream_asset_2],
    resources={"airflow_db": make_ephemeral_airflow_db_resource()},
)

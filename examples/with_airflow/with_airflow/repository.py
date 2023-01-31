import os

# start_repo_marker_0
from dagster_airflow import (load_assets_from_airflow_dag,
                             make_dagster_job_from_airflow_dag,
                             make_dagster_repo_from_airflow_dags_path,
                             make_dagster_repo_from_airflow_example_dags)
from with_airflow.airflow_complex_dag import complex_dag
from with_airflow.airflow_kubernetes_dag import kubernetes_dag
from with_airflow.airflow_simple_dag import simple_dag

from dagster import AssetKey, asset, repository

airflow_simple_dag = make_dagster_job_from_airflow_dag(simple_dag)
airflow_complex_dag = make_dagster_job_from_airflow_dag(complex_dag)
airflow_kubernetes_dag = make_dagster_job_from_airflow_dag(kubernetes_dag, mock_xcom=True)


@repository
def with_airflow():
    return [airflow_simple_dag, airflow_complex_dag, airflow_kubernetes_dag]

# end_repo_marker_0

@asset(
    group_name='simple_dag'
)
def new_upstream_asset_1():
    return 1

@asset(
    group_name='simple_dag'
)
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
        'sink_task_bar': {AssetKey('new_upstream_asset_1'), AssetKey('new_upstream_asset_2')},
        'get_task_instance_1_2': {AssetKey('new_upstream_asset_2')},
        'get_task_instance_2_2': {AssetKey('new_upstream_asset_2')},
    }
)


@repository
def sda_examples():
    return [simple_asset, new_upstream_asset_1, new_upstream_asset_2]


task_flow_repo = make_dagster_repo_from_airflow_dags_path(
    os.path.abspath("./with_airflow/task_flow_dags/"),
    "task_flow_repo",
)


airflow_examples_dags_repo = make_dagster_repo_from_airflow_example_dags()

# start_repo_marker_1

airflow_simple_dag_with_execution_date = make_dagster_job_from_airflow_dag(
    dag=simple_dag, tags={"airflow_execution_date": "2021-11-01 00:00:00+00:00"}
)
# end_repo_marker_1

import os
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow_shared.ecs import EcsRunTaskOperator
from dagster._time import get_current_datetime
from dagster_airlift.in_airflow import proxying_to_dagster
from dagster_airlift.in_airflow.proxied_state import load_proxied_state_from_yaml

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": get_current_datetime(),
    "retries": 0,
}


DBT_DIR = os.getenv("DBT_PROJECT_DIR")
args = f"--project-dir {DBT_DIR} --profiles-dir {DBT_DIR}"

dag = DAG(
    "operate_on_orders_data",
    default_args=default_args,
    # daily schedule interval
    schedule_interval="0 0 * * *",
    is_paused_upon_creation=False,
)
run_dbt_models = BashOperator(task_id="run_orders_models", bash_command=f"dbt run {args}", dag=dag)
bespoke_stuff = EcsRunTaskOperator(
    task_id="run_bespoke_in_isolated_env",
    dag=dag,
    overrides={
        "containerOverrides": [
            {
                "name": "my-container-name",
                "command": ["echo", "hello", "world"],
            },
        ],
    },
    cluster_name="my-cluster",
    task_definition={
        "family": "my-task-family",
        "containerDefinitions": [{"name": "my-container", "image": "my-image"}],
    },
)
run_dbt_models >> bespoke_stuff  # type: ignore

proxying_to_dagster(
    global_vars=globals(),
    proxied_state=load_proxied_state_from_yaml(Path(__file__).parent / "proxied_state"),
)

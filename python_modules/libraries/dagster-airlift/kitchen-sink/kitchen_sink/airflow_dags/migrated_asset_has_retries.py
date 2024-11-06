from pathlib import Path
from typing import Any, Mapping

from airflow import DAG
from airflow.operators.python import PythonOperator
from dagster._time import get_current_datetime_midnight
from dagster_airlift.in_airflow import DefaultProxyTaskToDagsterOperator, proxying_to_dagster
from dagster_airlift.in_airflow.dagster_run_utils import (
    MAX_RETRIES_TAG,
    RETRY_ON_ASSET_OR_OP_FAILURE_TAG,
)
from dagster_airlift.in_airflow.proxied_state import load_proxied_state_from_yaml


def print_hello() -> None:
    print("Hello")  # noqa: T201


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 0,
}


# Normally this isn't needed, but we're trying to get away with not using a multi-process-safe run storage
# to test behavior here.
class SetDagsterRetryInfoOperator(DefaultProxyTaskToDagsterOperator):
    def default_dagster_run_tags(self, context) -> Mapping[str, Any]:
        tags = {**super().default_dagster_run_tags(context), MAX_RETRIES_TAG: "3"}
        if self.get_airflow_dag_id(context).endswith("not_step_failure"):
            tags[RETRY_ON_ASSET_OR_OP_FAILURE_TAG] = "false"
        return tags


with DAG(
    dag_id="migrated_asset_has_retries",
    default_args=default_args,
    schedule=None,
    start_date=get_current_datetime_midnight(),
    # We pause this dag upon creation to avoid running it immediately
    is_paused_upon_creation=False,
) as minute_dag:
    PythonOperator(task_id="my_task", python_callable=print_hello)


with DAG(
    dag_id="migrated_asset_has_retries_not_step_failure",
    default_args=default_args,
    schedule=None,
    start_date=get_current_datetime_midnight(),
    # We pause this dag upon creation to avoid running it immediately
    is_paused_upon_creation=False,
) as minute_dag:
    PythonOperator(task_id="my_task", python_callable=print_hello)


proxying_to_dagster(
    proxied_state=load_proxied_state_from_yaml(Path(__file__).parent / "proxied_state"),
    global_vars=globals(),
    build_from_task_fn=SetDagsterRetryInfoOperator.build_from_task,
)

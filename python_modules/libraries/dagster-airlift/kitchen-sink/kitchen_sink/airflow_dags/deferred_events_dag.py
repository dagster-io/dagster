from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator
from dagster_airlift.in_airflow import proxying_to_dagster
from dagster_airlift.in_airflow.proxied_state import load_proxied_state_from_yaml
from dagster_airlift.in_airflow.task_proxy_operator import DefaultProxyTaskToDagsterOperator


class DeferredEventsTaskProxyOperator(DefaultProxyTaskToDagsterOperator):
    @property
    def should_defer_asset_events(self) -> bool:
        return True


def print_hello() -> None:
    print("Hello")  # noqa: T201


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2023, 1, 1),
    "retries": 0,
}


with DAG(
    "deferred_events_dag",
    default_args=default_args,
    schedule_interval=None,
    is_paused_upon_creation=False,
) as dag:
    PythonOperator(task_id="print_task", python_callable=print_hello) >> PythonOperator(
        task_id="downstream_print_task", python_callable=print_hello
    )  # type: ignore


proxying_to_dagster(
    proxied_state=load_proxied_state_from_yaml(Path(__file__).parent / "proxied_state"),
    global_vars=globals(),
    build_from_task_fn=DeferredEventsTaskProxyOperator.build_from_task,
)

from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.models import BaseOperator
from airflow.operators.python import PythonOperator
from dagster_airlift.in_airflow import DefaultProxyTaskToDagsterOperator, proxying_to_dagster
from dagster_airlift.in_airflow.proxied_state import load_proxied_state_from_yaml
from dagster_airlift.in_airflow.task_proxy_operator import (
    BaseProxyTaskToDagsterOperator,
    build_dagster_task,
)


def print_hello() -> None:
    print("Hello")  # noqa: T201


def build_print_task(task_id: str) -> PythonOperator:
    return PythonOperator(task_id=task_id, python_callable=print_hello, doc_md="Original doc")


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2023, 1, 1),
    "retries": 0,
}


with DAG(
    "affected_dag",
    default_args=default_args,
    schedule_interval=None,
    is_paused_upon_creation=False,
) as affected_dag:
    build_print_task("print_task") >> build_print_task("downstream_print_task")  # type: ignore

with DAG(
    "unaffected_dag",
    default_args=default_args,
    schedule_interval=None,
    is_paused_upon_creation=False,
) as unaffected_dag:
    build_print_task("print_task") >> build_print_task("downstream_print_task")  # type: ignore


class CustomProxyTaskToDagsterOperator(DefaultProxyTaskToDagsterOperator):
    @classmethod
    def build_from_task(cls, original_task: BaseOperator) -> BaseProxyTaskToDagsterOperator:
        """A custom callback to construct a new operator for the given task. In our case, we add retries to the affected_dag."""
        new_task = build_dagster_task(original_task, DefaultProxyTaskToDagsterOperator)
        if original_task.dag_id == "affected_dag":
            assert original_task.start_date
            new_task.retries = 1
        return new_task


proxying_to_dagster(
    proxied_state=load_proxied_state_from_yaml(Path(__file__).parent / "proxied_state"),
    global_vars=globals(),
    build_from_task_fn=CustomProxyTaskToDagsterOperator.build_from_task,
)

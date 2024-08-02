import logging
from datetime import datetime

from airflow import DAG
from dagster_airlift.in_airflow.dagster_operator import build_dagster_task

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.INFO)
requests_log.propagate = True


def print_hello():
    print("Hello")  # noqa: T201


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2023, 1, 1),
    "retries": 1,
}

dag = DAG(
    "the_dag", default_args=default_args, schedule_interval=None, is_paused_upon_creation=False
)
migrated_op = build_dagster_task(task_id="some_task", dag=dag)
other_migrated_op = build_dagster_task(task_id="other_task", dag=dag)

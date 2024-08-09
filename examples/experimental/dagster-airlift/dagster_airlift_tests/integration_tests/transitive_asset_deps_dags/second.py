from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2023, 1, 1),
    "retries": 1,
}

dag = DAG(
    "second", default_args=default_args, schedule_interval=None, is_paused_upon_creation=False
)
# Neither of these tasks have downstreams within the dag, so they should be considered "leaf" tasks.
# This task will have a downstream to first.two
one = PythonOperator(task_id="one", python_callable=lambda: None, dag=dag)
# This task will have a downstream to first.three
two = PythonOperator(task_id="two", python_callable=lambda: None, dag=dag)

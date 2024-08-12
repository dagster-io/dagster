from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2023, 1, 1),
    "retries": 1,
}

dag = DAG("first", default_args=default_args, schedule_interval=None, is_paused_upon_creation=False)
# This task will have a downstream to second.upstream_on_first
one = PythonOperator(task_id="one", python_callable=lambda: None, dag=dag)
# This task will have an upstream on second.only. Meaning first.one should not be considered a "leaf".
two = PythonOperator(task_id="two", python_callable=lambda: None, dag=dag)
# This task will have an upstream on second.only. Meaning first.one should not be considered a "leaf".
three = PythonOperator(task_id="three", python_callable=lambda: None, dag=dag)

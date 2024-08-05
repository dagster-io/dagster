from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

from ..business_logic import load_csv_to_duckdb

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2023, 1, 1),
    "retries": 1,
}

dag = DAG("load_lakehouse", default_args=default_args, schedule_interval=None)
load_iris = PythonOperator(task_id="load_iris", python_callable=load_csv_to_duckdb, dag=dag)

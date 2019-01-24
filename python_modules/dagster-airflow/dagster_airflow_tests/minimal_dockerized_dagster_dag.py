import errno
import os

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.dagster_plugin import ModifiedDockerOperator

from dagster_airflow.scaffold import scaffold_airflow_dag


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime.utcnow(),
    'email': ['airflow@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = scaffold_airflow_dag()

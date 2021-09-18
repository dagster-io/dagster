"""
The airflow DAG for

This file should go inside $AIRFLOW_HOME/dags
"""
import datetime

from dagster_airflow.factory import make_airflow_dag

DEFAULT_ARGS = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime.datetime(2019, 11, 7),
    "email": ["airflow@example.com"],
    "email_on_failure": False,
    "email_on_retry": False,
}

dag, tasks = make_airflow_dag(
    module_name="dagster_job",
    pipeline_name="cereals_job",
    dag_kwargs={"default_args": DEFAULT_ARGS, "max_active_runs": 1},
)

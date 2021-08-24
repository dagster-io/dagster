"""
The airflow DAG for hello_cereal_pipeline
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
    module_name="docs_snippets_crag.integrations.airflow.hello_cereal",
    pipeline_name="hello_cereal_pipeline",
    dag_kwargs={"default_args": DEFAULT_ARGS, "max_active_runs": 1},
)

# pylint: disable=unused-variable

import datetime

from dagster_airflow.factory import make_airflow_dag_containerized

DEFAULT_ARGS = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime.datetime(2019, 11, 7),
    "email": ["airflow@example.com"],
    "email_on_failure": False,
    "email_on_retry": False,
}

dag, steps = make_airflow_dag_containerized(
    module_name="docs_snippets.integrations.airflow.hello_cereal",
    job_name="hello_cereal_job",
    image="dagster-airflow-demo-repository",
    dag_kwargs={"default_args": DEFAULT_ARGS, "max_active_runs": 1},
)

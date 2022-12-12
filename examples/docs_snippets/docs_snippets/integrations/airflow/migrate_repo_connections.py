import os

from airflow.models import Connection
from dagster_airflow import make_dagster_repo_from_airflow_dags_path

migrated_airflow_repo = make_dagster_repo_from_airflow_dags_path(
    os.path.join(os.environ["AIRFLOW_HOME"], "dags"),
    "migrated_airflow_repo",
    connections=[
        Connection(conn_id="http_default", conn_type="uri", host="https://google.com")
    ],
)

import os

from airflow.models import Connection
from dagster_airflow import make_dagster_definitions_from_airflow_dags_path

migrated_airflow_definitions = make_dagster_definitions_from_airflow_dags_path(
    os.path.abspath("./dags/"),
    connections=[
        Connection(conn_id="http_default", conn_type="uri", host="https://google.com")
    ],
)

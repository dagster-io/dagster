import os

from dagster_airflow import make_dagster_repo_from_airflow_dags_path

migrated_airflow_repo = make_dagster_repo_from_airflow_dags_path(
    os.path.join(os.environ["AIRFLOW_HOME"], "dags"),
    "migrated_airflow_repo",
)

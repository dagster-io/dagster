import os
from pathlib import Path

from dagster_airlift.core import AirflowInstance, BasicAuthBackend, build_defs_from_airflow_instance

from .build_dag_defs import build_dag_defs
from .constants import AIRFLOW_BASE_URL, AIRFLOW_INSTANCE_NAME, PASSWORD, USERNAME

airflow_instance = AirflowInstance(
    auth_backend=BasicAuthBackend(
        webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
    ),
    name=AIRFLOW_INSTANCE_NAME,
)


def dbt_project_path() -> Path:
    env_val = os.getenv("DBT_PROJECT_DIR")
    assert env_val
    return Path(env_val)


defs = build_defs_from_airflow_instance(
    airflow_instance=airflow_instance,
    defs=build_dag_defs(
        duckdb_path=Path(os.environ["AIRFLOW_HOME"]) / "jaffle_shop.duckdb",
        dbt_project_path=dbt_project_path(),
    ),
)

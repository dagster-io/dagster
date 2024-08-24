from dagster_airlift.core import (
    AirflowInstance,
    BasicAuthBackend,
    combine_defs,
    sync_build_defs_from_airflow_instance,
)
from dagster_airlift.dbt import defs_from_airflow_dbt
from dagster_dbt import DbtProject

from dbt_example.dagster_defs.lakehouse import defs_from_lakehouse, lakehouse_existence_check
from dbt_example.shared.load_iris import CSV_PATH, DB_PATH, IRIS_COLUMNS

from .constants import (
    AIRFLOW_BASE_URL,
    AIRFLOW_INSTANCE_NAME,
    PASSWORD,
    USERNAME,
    dbt_manifest_path,
    dbt_project_path,
)

airflow_instance = AirflowInstance(
    auth_backend=BasicAuthBackend(
        webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
    ),
    name=AIRFLOW_INSTANCE_NAME,
)


defs = sync_build_defs_from_airflow_instance(
    airflow_instance=airflow_instance,
    defs=combine_defs(
        defs_from_lakehouse(
            dag_id="load_lakehouse",
            task_id="load_iris",
            csv_path=CSV_PATH,
            duckdb_path=DB_PATH,
            columns=IRIS_COLUMNS,
        ),
        defs_from_airflow_dbt(
            dag_id="dbt_dag",
            task_id="build_dbt_models",
            manifest=dbt_manifest_path(),
            project=DbtProject(dbt_project_path()),
        ),
        lakehouse_existence_check(
            csv_path=CSV_PATH,
            duckdb_path=DB_PATH,
        ),
    ),
)

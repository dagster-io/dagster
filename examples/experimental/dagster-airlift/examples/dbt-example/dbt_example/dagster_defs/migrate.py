from dagster._core.definitions.definitions_class import Definitions
from dagster_airlift.core import (
    AirflowInstance,
    BasicAuthBackend,
    build_defs_from_airflow_instance,
    dag_defs,
    task_defs,
)
from dagster_airlift.dbt import dbt_defs
from dagster_dbt import DbtProject

from dbt_example.dagster_defs.lakehouse import (
    defs_from_lakehouse,
    lakehouse_existence_check_defs,
    specs_from_lakehouse,
)
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


defs = build_defs_from_airflow_instance(
    airflow_instance=airflow_instance,
    defs=Definitions.merge(
        dag_defs(
            "rebuild_iris_models",
            task_defs(
                "load_iris",
                defs_from_lakehouse(
                    specs=specs_from_lakehouse(csv_path=CSV_PATH),
                    csv_path=CSV_PATH,
                    duckdb_path=DB_PATH,
                    columns=IRIS_COLUMNS,
                ),
            ),
            task_defs(
                "build_dbt_models",
                dbt_defs(
                    manifest=dbt_manifest_path(),
                    project=DbtProject(dbt_project_path()),
                ),
            ),
        ),
        lakehouse_existence_check_defs(
            csv_path=CSV_PATH,
            duckdb_path=DB_PATH,
        ),
    ),
)

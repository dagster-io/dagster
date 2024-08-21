from dagster_airlift.core import AirflowInstance, BasicAuthBackend, build_defs_from_airflow_instance
from dagster_airlift.core.def_factory import defs_from_factories
from dagster_airlift.dbt import DbtProjectDefs

from dbt_example.dagster_defs.csv_to_duckdb_defs import CSVToDuckdbDefs

from .constants import AIRFLOW_BASE_URL, AIRFLOW_INSTANCE_NAME, PASSWORD, USERNAME, dbt_project_path

airflow_instance = AirflowInstance(
    auth_backend=BasicAuthBackend(
        webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
    ),
    name=AIRFLOW_INSTANCE_NAME,
)


defs = build_defs_from_airflow_instance(
    airflow_instance=airflow_instance,
    orchestrated_defs=defs_from_factories(
        CSVToDuckdbDefs(
            name="load_lakehouse__load_iris",
            table_name="iris_lakehouse_table",
            duckdb_schema="iris_dataset",
        ),
        DbtProjectDefs(
            name="dbt_dag__build_dbt_models",
            dbt_manifest=dbt_project_path() / "target" / "manifest.json",
        ),
    ),
)

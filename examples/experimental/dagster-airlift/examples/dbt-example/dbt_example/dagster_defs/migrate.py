import os
from pathlib import Path

from dagster_airlift.core import AirflowInstance, BasicAuthBackend, build_defs_from_airflow_instance
from dagster_airlift.core.def_factory import defs_from_factories
from dagster_airlift.dbt import DbtProjectDefs
from dagster_dbt import DbtProject

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
            csv_path=Path("iris.csv"),
            duckdb_path=Path(os.environ["AIRFLOW_HOME"]) / "jaffle_shop.duckdb",
            column_names=[
                "sepal_length_cm",
                "sepal_width_cm",
                "petal_length_cm",
                "petal_width_cm",
                "species",
            ],
            duckdb_schema="iris_dataset",
            duckdb_database_name="jaffle_shop",
        ),
        DbtProjectDefs(
            name="dbt_dag__build_dbt_models",
            dbt_manifest=dbt_project_path() / "target" / "manifest.json",
            project=DbtProject(project_dir=dbt_project_path()),
        ),
    ),
)

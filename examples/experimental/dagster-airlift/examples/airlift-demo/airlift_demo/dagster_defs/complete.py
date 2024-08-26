from dagster import Definitions
from dagster_airlift.dbt import dbt_defs
from dagster_dbt import DbtProject

from airlift_demo.dagster_defs.lakehouse import (
    defs_from_lakehouse,
    lakehouse_existence_check_defs,
    specs_from_lakehouse,
)
from airlift_demo.shared.load_iris import CSV_PATH, DB_PATH, IRIS_COLUMNS

from .constants import dbt_manifest_path, dbt_project_path

defs = Definitions.merge(
    defs_from_lakehouse(
        specs=specs_from_lakehouse(csv_path=CSV_PATH),
        csv_path=CSV_PATH,
        duckdb_path=DB_PATH,
        columns=IRIS_COLUMNS,
    ),
    dbt_defs(
        manifest=dbt_manifest_path(),
        project=DbtProject(dbt_project_path()),
    ),
    lakehouse_existence_check_defs(
        csv_path=CSV_PATH,
        duckdb_path=DB_PATH,
    ),
)

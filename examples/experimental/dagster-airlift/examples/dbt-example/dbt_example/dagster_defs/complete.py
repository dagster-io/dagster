from dagster_airlift.core import combine_defs
from dagster_airlift.dbt import dbt_defs
from dagster_dbt import DbtProject

from dbt_example.dagster_defs.lakehouse import (
    defs_from_lakehouse,
    lakehouse_existence_check,
    specs_from_lakehouse,
)
from dbt_example.shared.load_iris import CSV_PATH, DB_PATH, IRIS_COLUMNS

from .constants import dbt_manifest_path, dbt_project_path

defs = combine_defs(
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
    lakehouse_existence_check(
        csv_path=CSV_PATH,
        duckdb_path=DB_PATH,
    ),
)

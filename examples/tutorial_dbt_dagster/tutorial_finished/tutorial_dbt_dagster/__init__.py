import os

from dagster import Definitions, load_assets_from_modules
from dagster_dbt import dbt_cli_resource
from dagster_duckdb_pandas import duckdb_pandas_io_manager

from tutorial_dbt_dagster import assets
from tutorial_dbt_dagster.assets import DBT_PROFILES, DBT_PROJECT_PATH

resources = {
    "dbt": dbt_cli_resource.configured(
        {
            "project_dir": DBT_PROJECT_PATH,
            "profiles_dir": DBT_PROFILES,
        },
    ),
    "io_manager": duckdb_pandas_io_manager.configured(
        {"database": os.path.join(DBT_PROJECT_PATH, "tutorial.duckdb")}
    ),
}

defs = Definitions(assets=load_assets_from_modules([assets]), resources=resources)

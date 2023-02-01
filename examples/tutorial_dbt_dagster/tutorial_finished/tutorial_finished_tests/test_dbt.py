from dagster_dbt import dbt_cli_resource
from dagster_duckdb_pandas import duckdb_pandas_io_manager
from tutorial_dbt_dagster.assets import (
    DBT_PROFILES,
    DBT_PROJECT_PATH,
    all_assets_job,
)
from tutorial_dbt_dagster import assets
from dagster import with_resources, load_assets_from_package_module
import os


def test_everything():
    resolved_assets = with_resources(
        load_assets_from_package_module(assets),
        {
            "dbt": dbt_cli_resource.configured(
                {
                    "project_dir": DBT_PROJECT_PATH,
                    "profiles_dir": DBT_PROFILES,
                },
            ),
            "duckdb": duckdb_pandas_io_manager.configured(
                {"database": os.path.join(DBT_PROJECT_PATH, "tutorial.duckdb")}
            ),
        },
    )

    resolved_job = all_assets_job.resolve(resolved_assets, [])

    result = resolved_job.execute_in_process()

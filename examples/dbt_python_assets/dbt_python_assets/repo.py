import os
from typing import Any, Tuple

import dbt_python_assets.forecasting as forecasting
import dbt_python_assets.raw_data as raw_data
from dagster_dbt import dbt_cli_resource, load_assets_from_dbt_project
from dbt_python_assets.resources import duckdb_io_manager

from dagster import (
    define_asset_job,
    fs_io_manager,
    load_assets_from_package_module,
    repository,
    with_resources,
)
from dagster.utils import file_relative_path

DBT_PROJECT_DIR = file_relative_path(__file__, "../dbt_project")
DBT_PROFILES_DIR = file_relative_path(__file__, "../dbt_project/config")

# all assets live in the default dbt_schema
dbt_assets = load_assets_from_dbt_project(
    DBT_PROJECT_DIR,
    DBT_PROFILES_DIR,
    # prefix the output assets based on the database they live in
    # plus the name of the schema
    key_prefix=["duckdb", "dbt"],
    # prefix the source assets based on just the database
    # (dagster populates the source schema information automatically)
    source_key_prefix=["duckdb"],
)

raw_data_assets = load_assets_from_package_module(
    raw_data,
    group_name="raw_data",
    # all of these assets live in the duckdb database, under the schema raw_data
    key_prefix=["duckdb", "raw_data"],
)

forecasting_assets = load_assets_from_package_module(
    forecasting,
    group_name="forecasting",
)


@repository
def example_repo():
    return with_resources(
        dbt_assets + raw_data_assets + forecasting_assets,
        resource_defs={
            "io_manager": duckdb_io_manager.configured(
                {"duckdb_path": os.path.join(DBT_PROJECT_DIR, "example.duckdb")}
            ),
            "model_io_manager": fs_io_manager,
            "dbt": dbt_cli_resource.configured(
                {"project_dir": DBT_PROJECT_DIR, "profiles_dir": DBT_PROFILES_DIR}
            ),
        },
    ) + [
        define_asset_job("everything_everywhere", selection="*"),
        define_asset_job("refresh_forecast_model", selection="*order_forecast_model"),
    ]

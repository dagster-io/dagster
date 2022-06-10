import os
from typing import Any, Tuple

from dagster_dbt import dbt_cli_resource, load_assets_from_dbt_project

from dagster import load_assets_from_package_module, repository, with_resources, define_asset_job
from dagster.core.asset_defs.load_assets_from_modules import prefix_assets
from dagster.utils import file_relative_path

from dbt_python_assets.resources import duckdb_io_manager

import dbt_python_assets.forecasting as forecasting
import dbt_python_assets.raw_data as raw_data

DBT_PROJECT_DIR = file_relative_path(__file__, "../dbt_project")
DBT_PROFILES_DIR = file_relative_path(__file__, "../dbt_project/config")

# all assets live in the default dbt_schema
dbt_assets = prefix_assets(
    load_assets_from_dbt_project(
        DBT_PROJECT_DIR,
        DBT_PROFILES_DIR,
    ),
    key_prefix="dbt_schema",
)

raw_data_assets = load_assets_from_package_module(
    raw_data,
    group_name="raw_data",
    key_prefix=["raw_data"],
)

all_assets = prefix_assets(dbt_assets + raw_data_assets, key_prefix="duckdb")

forecasting_assets = load_assets_from_package_module(
    forecasting,
    group_name="forecasting",
)


@repository
def example_repo():
    return with_resources(
        all_assets + forecasting_assets,
        # dbt_assets + raw_data_assets + forecasting_assets,
        resource_defs={
            "io_manager": duckdb_io_manager.configured(
                {"duckdb_path": os.path.join(DBT_PROJECT_DIR, "example.duckdb")}
            ),
            "dbt": dbt_cli_resource.configured(
                {"project_dir": DBT_PROJECT_DIR, "profiles_dir": DBT_PROFILES_DIR}
            ),
        },
    ) + [define_asset_job("foo", selection="*")]

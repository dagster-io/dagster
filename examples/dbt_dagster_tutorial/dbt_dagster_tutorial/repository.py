import os

from dagster_dbt import dbt_cli_resource
from dbt_dagster_tutorial.assets import (
    DBT_PROFILES,
    DBT_PROJECT_PATH,
    customers_raw,
    dbt_assets,
    order_count_chart,
    orders_raw,
)
from dbt_dagster_tutorial.duckdb_resource import duckdb_io_manager

from dagster import repository, with_resources


@repository
def jaffle_shop_repository():
    return with_resources(
        [
            customers_raw,
            orders_raw,
            *dbt_assets,
            order_count_chart,
        ],  # we could swap this out with a fn that loads all assets from a file/module
        {
            "dbt": dbt_cli_resource.configured(
                {
                    "project_dir": DBT_PROJECT_PATH,
                    "profiles_dir": DBT_PROFILES,
                },
            ),
            "io_manager": duckdb_io_manager.configured(
                {"duckdb_path": os.path.join(DBT_PROJECT_PATH, "tutorial.duckdb")}
            ),
        },
    )

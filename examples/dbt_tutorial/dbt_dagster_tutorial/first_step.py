import os
import pandas as pd

from dagster_dbt import load_assets_from_dbt_project, dbt_cli_resource
from dagster import repository, with_resources, asset, AssetIn, fs_io_manager, Output, MetadataValue
from dagster._utils import file_relative_path

from dbt_dagster_tutorial.duckdb_resource import duckdb_io_manager



@asset(
    key_prefix=["duckdb", "raw_data"],
    group_name="staging"
)
def customers() -> pd.DataFrame:
    data = pd.read_csv('s3://dbt-tutorial-public/jaffle_shop_customers.csv')
    return data

@asset(
    key_prefix=["duckdb", "raw_data"],
    group_name="staging"
)
def orders() -> pd.DataFrame:
    data = pd.read_csv('s3://dbt-tutorial-public/jaffle_shop_orders.csv')
    return data


DBT_PROJECT_PATH=file_relative_path(__file__, "../jaffle_shop")
DBT_PROFILES=file_relative_path(__file__, "../jaffle_shop/config")

dbt_assets = load_assets_from_dbt_project(project_dir=DBT_PROJECT_PATH, profiles_dir=DBT_PROFILES, key_prefix=["duckdb", "jaffle_shop"], source_key_prefix=["duckdb"])

@repository
def jaffle_shop_repository():
    return with_resources(
            [customers, orders, *dbt_assets],
            {
                "dbt": dbt_cli_resource.configured(
                    {
                        "project_dir": DBT_PROJECT_PATH,
                        "profiles_dir": DBT_PROFILES,
                    },
                ),
                "io_manager": duckdb_io_manager.configured(
                    {"duckdb_path": os.path.join(DBT_PROJECT_PATH, "example.duckdb")}
                ),
                "fs_io_manager": fs_io_manager,
            },
        )
import os
import pandas as pd
import plotly.express as px
import plotly.offline as po

from dagster_dbt import load_assets_from_dbt_project, dbt_cli_resource
from dagster import repository, with_resources, asset, AssetIn, fs_io_manager, Output
from dagster._utils import file_relative_path

from dbt_dagster_tutorial.duckdb_resource import duckdb_io_manager
from dbt_dagster_tutorial.assets import DBT_PROFILES, DBT_PROJECT_PATH, customers, orders, dbt_assets, order_count_chart

@repository
def jaffle_shop_repository():
    return with_resources(
            [customers, orders, *dbt_assets, order_count_chart],
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
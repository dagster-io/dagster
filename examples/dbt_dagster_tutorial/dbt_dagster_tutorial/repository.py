import os

import pandas as pd
import plotly.express as px
import plotly.offline as po
from dagster_dbt import dbt_cli_resource, load_assets_from_dbt_project
from dbt_dagster_tutorial.assets import (
    DBT_PROFILES,
    DBT_PROJECT_PATH,
    customers,
    dbt_assets,
    order_count_chart,
    orders,
)
from dbt_dagster_tutorial.duckdb_resource import duckdb_io_manager

from dagster import AssetIn, Output, asset, fs_io_manager, repository, with_resources
from dagster._utils import file_relative_path


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
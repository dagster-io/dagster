import os
import pandas as pd
import plotly.express as px
import plotly.offline as po

from dagster_dbt import load_assets_from_dbt_project, dbt_cli_resource
from dagster import repository, with_resources, asset, AssetIn, fs_io_manager, Output, MetadataValue
from dagster._utils import file_relative_path

from dagster_snowflake import build_snowflake_io_manager
from dagster_snowflake_pandas import SnowflakePandasTypeHandler

from dbt_dagster_tutorial.duckdb_resource import duckdb_io_manager

snowflake_io_manager = build_snowflake_io_manager([SnowflakePandasTypeHandler()])


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
print(DBT_PROFILES)
print(DBT_PROJECT_PATH)

dbt_assets = load_assets_from_dbt_project(project_dir=DBT_PROJECT_PATH, profiles_dir=DBT_PROFILES, key_prefix=["duckdb", "jaffle_shop"], source_key_prefix=["duckdb"])

@asset(
    ins={"customers": AssetIn(key_prefix=["duckdb", "jaffle_shop"])},
    group_name="staging",
    io_manager_key="fs_io_manager",
    key_prefix=["duckdb", "jaffle_shop"]
)
def order_count_chart(customers: pd.DataFrame):
    fig = px.histogram(customers, x="number_of_orders")
    fig.update_layout(bargap=0.2)
    plot_html = po.plot(fig)

    return plot_html


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
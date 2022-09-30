import os

import pandas as pd
import plotly.express as px
import plotly.offline as po
from dagster_dbt import dbt_cli_resource, load_assets_from_dbt_project

from dagster import AssetIn, Output, asset, fs_io_manager, repository, with_resources, MetadataValue
from dagster._utils import file_relative_path


# These assets would be part of the first stage of the tutorial
@asset(
    key_prefix=["duckdb", "raw_data"],
    group_name="staging"
)
def customers() -> pd.DataFrame:
    data = pd.read_csv('s3://dbt-tutorial-public/jaffle_shop_customers.csv')
    # data = pd.read_csv("https://docs.dagster.io/assets/customers.csv") TODO replace ^ with this
    return data

@asset(
    key_prefix=["duckdb", "raw_data"],
    group_name="staging"
)
def orders() -> pd.DataFrame:
    data = pd.read_csv('s3://dbt-tutorial-public/jaffle_shop_orders.csv')
    # data = pd.read_csv("https://docs.dagster.io/assets/orders.csv") TODO replace ^ with this
    return data


DBT_PROJECT_PATH=file_relative_path(__file__, "../jaffle_shop")
DBT_PROFILES=file_relative_path(__file__, "../jaffle_shop/config")

# if larger project use load_assets_from_dbt_manifest
# dbt_assets = load_assets_from_dbt_manifest(json.load(DBT_PROJECT_PATH + "manifest.json", encoding="utf8"))
dbt_assets = load_assets_from_dbt_project(project_dir=DBT_PROJECT_PATH, profiles_dir=DBT_PROFILES, key_prefix=["duckdb", "jaffle_shop"], source_key_prefix=["duckdb"])

# end first stage of tutorial - at this point you can run dagit and launch a materialization

# This asset would be the second stage of the tutorial
@asset(
    ins={"customers": AssetIn(key_prefix=["duckdb", "jaffle_shop"])},
    group_name="staging",
    io_manager_key="fs_io_manager",
    key_prefix=["duckdb", "jaffle_shop"]
)
def order_count_chart(customers: pd.DataFrame):
    fig = px.histogram(customers, x="number_of_orders")
    fig.update_layout(bargap=0.2)
    plot_html = fig.write_html(file_relative_path(__file__, "order_count_chart.html"), auto_open=True)

    # return plot html as metadata ex file:///Users/jamie/dev/dagster/examples/dbt_tutorial/temp-plot.html
    return Output(None, metadata={"plot_url": MetadataValue.url("file://" + file_relative_path(__file__, "order_count_chart.html"))})
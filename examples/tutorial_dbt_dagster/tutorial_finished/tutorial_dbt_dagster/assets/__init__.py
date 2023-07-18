import pandas as pd
import plotly.express as px
from dagster import AssetKey, MetadataValue, asset, file_relative_path
from dagster_dbt import load_assets_from_dbt_project
from dagster_duckdb import DuckDBResource


@asset(key_prefix=["jaffle_shop"])
def customers_raw(duckdb: DuckDBResource) -> None:
    pd.read_csv("https://docs.dagster.io/assets/customers.csv")
    with duckdb.get_connection() as conn:
        conn.execute("create table if not exists jaffle_shop.customers_raw as select * from data;")


@asset(key_prefix=["jaffle_shop"])
def orders_raw(duckdb: DuckDBResource) -> None:
    pd.read_csv("https://docs.dagster.io/assets/orders.csv")
    with duckdb.get_connection() as conn:
        conn.execute("create table if not exists jaffle_shop.orders_raw as select * from data;")


DBT_PROJECT_PATH = file_relative_path(__file__, "../../jaffle_shop")

# if larger project use load_assets_from_dbt_manifest
# dbt_assets = load_assets_from_dbt_manifest(json.load(DBT_PROJECT_PATH + "manifest.json", encoding="utf8"))
dbt_assets = load_assets_from_dbt_project(project_dir=DBT_PROJECT_PATH)


@asset(deps=[AssetKey("customers")])
def order_count_chart(context, duckdb: DuckDBResource) -> None:
    with duckdb.get_connection() as conn:
        customers = conn.execute("select * from jaffle_shop.customers").fetchdf()
    fig = px.histogram(customers, x="number_of_orders")
    fig.update_layout(bargap=0.2)
    save_chart_path = file_relative_path(__file__, "order_count_chart.html")
    fig.write_html(save_chart_path, auto_open=True)

    context.add_output_metadata({"plot_url": MetadataValue.url("file://" + save_chart_path)})

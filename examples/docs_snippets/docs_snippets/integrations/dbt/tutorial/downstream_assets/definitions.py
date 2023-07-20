# start_imports
import os
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
from dagster_dbt import (
    DbtCliResource,
    build_schedule_from_dbt_selection,
    dbt_assets,
    get_asset_key_for_model,
)

from dagster import Definitions, MetadataValue, OpExecutionContext, asset

# end_imports


dbt_project_dir = Path(__file__).parent.joinpath("..", "..")
duckdb_database_path = dbt_project_dir.joinpath("tutorial.duckdb")


@asset
def raw_customers(context) -> None:
    data = pd.read_csv("https://docs.dagster.io/assets/customers.csv")
    connection = duckdb.connect(os.fspath(duckdb_database_path))
    connection.execute("create schema if not exists jaffle_shop")
    connection.execute(
        "create or replace table jaffle_shop.raw_customers as select * from data"
    )

    # Log some metadata about the table we just wrote. It will show up in the UI.
    context.add_output_metadata({"num_rows": data.shape[0]})


dbt = DbtCliResource(project_dir=os.fspath(dbt_project_dir))

# If DAGSTER_DBT_PARSE_PROJECT_ON_LOAD is set, a manifest will be created at runtime.
# Otherwise, we expect a manifest to be present in the project's target directory.
if os.getenv("DAGSTER_DBT_PARSE_PROJECT_ON_LOAD"):
    dbt_parse_invocation = dbt.cli(["parse"], manifest={}).wait()
    dbt_manifest_path = dbt_parse_invocation.target_path.joinpath("manifest.json")
else:
    dbt_manifest_path = dbt_project_dir.joinpath("target", "manifest.json")


@dbt_assets(manifest=dbt_manifest_path)
def jaffle_shop_dbt_assets(context: OpExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


schedules = [
    build_schedule_from_dbt_selection(
        [jaffle_shop_dbt_assets],
        job_name="materialize_dbt_models",
        cron_schedule="0 0 * * *",
        dbt_select="fqn:*",
    )
]


# start_downstream_asset
@asset(deps=get_asset_key_for_model([jaffle_shop_dbt_assets], "customers"))
def order_count_chart(context):
    # read the contents of the customers table into a Pandas DataFrame
    connection = duckdb.connect(os.fspath(duckdb_database_path))
    customers = connection.sql("select * from customers").df()

    # create a plot of number of orders by customer and write it out to an HTML file
    fig = px.histogram(customers, x="number_of_orders")
    fig.update_layout(bargap=0.2)
    save_chart_path = duckdb_database_path.parent.joinpath("order_count_chart.html")
    fig.write_html(save_chart_path, auto_open=True)

    # tell Dagster about the location of the HTML file,
    # so it's easy to access from the Dagster UI
    context.add_output_metadata(
        {"plot_url": MetadataValue.url("file://" + os.fspath(save_chart_path))}
    )


# end_downstream_asset


# start_defs
defs = Definitions(
    assets=[raw_customers, jaffle_shop_dbt_assets, order_count_chart],
    schedules=schedules,
    resources={
        "dbt": dbt,
    },
)

# end_defs

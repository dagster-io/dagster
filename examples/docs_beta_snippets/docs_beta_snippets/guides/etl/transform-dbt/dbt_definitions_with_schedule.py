import dagster as dg
from dagster_dbt import (
    dbt_assets,
    DbtCliResource,
    DbtProject,
    get_asset_key_for_model,
    # highlight-next-line
    build_schedule_from_dbt_selection,
)
from pathlib import Path
import plotly.express as px
from pathlib import Path
import pandas as pd
import duckdb
import os

duckdb_database_path = "basic-dbt-project/dev.duckdb"

@dg.asset(compute_kind="python")
def raw_customers(context: dg.AssetExecutionContext) -> None:
    # Pull customer data from a CSV
    data = pd.read_csv("https://docs.dagster.io/assets/customers.csv")
    connection = duckdb.connect(os.fspath(duckdb_database_path))

    # Create a schema named raw
    connection.execute("create schema if not exists raw")

    # Create/replace table named raw_customers
    connection.execute(
        "create or replace table raw.raw_customers as select * from data"
    )

    # Log some metadata about the new table. It will show up in the UI.
    context.add_output_metadata({"num_rows": data.shape[0]})


dbt_project_directory = Path(__file__).absolute().parent / "basic-dbt-project"
dbt_project = DbtProject(project_dir=dbt_project_directory)
dbt_resource = DbtCliResource(project_dir=dbt_project)
dbt_project.prepare_if_dev()


@dbt_assets(manifest=dbt_project.manifest_path)
def dbt_models(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


@dg.asset(
    compute_kind="python",
    # Defines the dependency on the customers model,
    # which is represented as an asset in Dagster
    deps=get_asset_key_for_model([dbt_models], "customers"),
)
def customer_histogram(context: dg.AssetExecutionContext):
    # Read the contents of the customers table into a Pandas DataFrame
    connection = duckdb.connect(os.fspath(duckdb_database_path))
    customers = connection.sql("select * from customers").df()

    # Create a customer histogram and write it out to an HTML file
    fig = px.histogram(customers, x="FIRST_NAME")
    fig.update_layout(bargap=0.2)
    fig.update_xaxes(categoryorder="total ascending")
    save_chart_path = Path(duckdb_database_path).parent.joinpath(
        "order_count_chart.html"
    )
    fig.write_html(save_chart_path, auto_open=True)

    # Tell Dagster about the location of the HTML file,
    # so it's easy to access from the Dagster UI
    context.add_output_metadata(
        {"plot_url": dg.MetadataValue.url("file://" + os.fspath(save_chart_path))}
    )


# highlight-start
# Build a schedule for the job that materializes a selection of dbt assets
dbt_schedule = build_schedule_from_dbt_selection(
    [dbt_models],
    job_name="materialize_dbt_models",
    cron_schedule="0 0 * * *",
    dbt_select="fqn:*",
)
# highlight-end


# Add Dagster definitions to Definitions object
defs = dg.Definitions(
    assets=[raw_customers, dbt_models, customer_histogram],
    resources={"dbt": dbt_resource},
    # highlight-next-line
    schedules=[dbt_schedule],
)

import dagster as dg
from dagster_dbt import dbt_assets, DbtCliResource, DbtProject
from pathlib import Path

# highlight-start
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
# highlight-end

dbt_project_directory = Path(__file__).absolute().parent / "basic-dbt-project"
dbt_project = DbtProject(project_dir=dbt_project_directory)
dbt_resource = DbtCliResource(project_dir=dbt_project)
dbt_project.prepare_if_dev()


@dbt_assets(manifest=dbt_project.manifest_path)
def dbt_models(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


# Add Dagster definitions to Definitions object
defs = dg.Definitions(
    # highlight-start
    assets=[raw_customers, dbt_models],
    # highlight-end
    resources={"dbt": dbt_resource},
)

if __name__ == "__main__":
    dg.materialize(assets=[raw_customers, dbt_models], resources={"dbt": dbt_resource})

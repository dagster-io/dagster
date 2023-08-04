# start_python_assets
import os
from pathlib import Path

import duckdb
import pandas as pd
from dagster_dbt import DbtCliResource, build_schedule_from_dbt_selection, dbt_assets

from dagster import Definitions, OpExecutionContext, asset

dbt_project_dir = Path(__file__).joinpath("..", "..", "..").resolve()
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
# end_python_assets

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

# start_defs
defs = Definitions(
    assets=[raw_customers, jaffle_shop_dbt_assets],
    schedules=schedules,
    resources={
        "dbt": dbt,
    },
)

# end_defs

import os

import duckdb
import pandas as pd

import dagster as dg


@dg.asset(key="raw_customers", compute_kind="python")
def raw_customers(context: dg.AssetExecutionContext) -> None:
    """Ingest raw customer data from an external source."""
    data = pd.read_csv("https://docs.dagster.io/assets/customers.csv")
    connection = duckdb.connect(os.fspath("dbt/dev.duckdb"))
    connection.execute("CREATE SCHEMA IF NOT EXISTS raw")
    connection.execute(
        "CREATE OR REPLACE TABLE raw.raw_customers AS SELECT * FROM data"
    )
    context.add_output_metadata({"num_rows": data.shape[0]})


@dg.asset(key="raw_orders", compute_kind="python")
def raw_orders(context: dg.AssetExecutionContext) -> None:
    """Ingest raw orders data from an external source."""
    data = pd.read_csv("https://docs.dagster.io/assets/orders.csv")
    with duckdb.connect(os.fspath("dbt/dev.duckdb")) as connection:
        connection.execute("CREATE SCHEMA IF NOT EXISTS raw")
        connection.execute(
            "CREATE OR REPLACE TABLE raw.raw_orders AS SELECT * FROM data"
        )
    context.add_output_metadata({"num_rows": data.shape[0]})

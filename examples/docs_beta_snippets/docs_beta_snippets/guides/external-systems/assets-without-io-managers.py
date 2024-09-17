import pandas as pd
from dagster_duckdb import DuckDBResource

import dagster as dg

raw_sales_data = dg.AssetSpec("raw_sales_data")


@dg.asset
def raw_sales_data(duckdb: DuckDBResource) -> None:
    # Read data from a CSV
    raw_df = pd.read_csv(
        "https://raw.githubusercontent.com/dagster-io/dagster/master/docs/next/public/assets/raw_sales_data.csv"
    )
    # Construct DuckDB connection
    with duckdb.get_connection() as conn:
        # Use the data from the CSV to create or update a table
        conn.execute(
            "CREATE TABLE IF NOT EXISTS raw_sales_data AS SELECT * FROM raw_df"
        )
        if not conn.fetchall():
            conn.execute("INSERT INTO raw_sales_data SELECT * FROM raw_df")


# Asset dependent on `raw_sales_data` asset
@dg.asset(deps=[raw_sales_data])
def clean_sales_data(duckdb: DuckDBResource) -> None:
    # Construct DuckDB connection
    with duckdb.get_connection() as conn:
        # Select data from table
        df = conn.execute("SELECT * FROM raw_sales_data").fetch_df()

        # Apply transform
        clean_df = df.fillna({"amount": 0.0})

        # Use transformed result to create or update a table
        conn.execute(
            "CREATE TABLE IF NOT EXISTS clean_sales_data AS SELECT * FROM clean_df"
        )
        if not conn.fetchall():
            conn.execute("INSERT INTO clean_sales_data SELECT * FROM clean_df")


# Asset dependent on `clean_sales_data` asset
@dg.asset(deps=[clean_sales_data])
def sales_summary(duckdb: DuckDBResource) -> None:
    # Construct DuckDB connection
    with duckdb.get_connection() as conn:
        # Select data from table
        df = conn.execute("SELECT * FROM clean_sales_data").fetch_df()

        # Apply transform
        summary = df.groupby(["owner"])["amount"].sum().reset_index()

        # Use transformed result to create or update a table
        conn.execute(
            "CREATE TABLE IF NOT EXISTS sales_summary AS SELECT * from summary"
        )
        if not conn.fetchall():
            conn.execute("INSERT INTO sales_summary SELECT * from summary")


defs = dg.Definitions(
    assets=[raw_sales_data, clean_sales_data, sales_summary],
    resources={"duckdb": DuckDBResource(database="sales.duckdb", schema="public")},
)

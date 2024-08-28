import pandas as pd
from dagster_duckdb import DuckDBResource

import dagster as dg

raw_sales_data = dg.AssetSpec("raw_sales_data")


@dg.asset
def raw_sales_data(duckdb: DuckDBResource) -> None:
    raw_df = pd.read_csv(
        "https://raw.githubusercontent.com/dagster-io/dagster/master/docs/next/public/assets/raw_sales_data.csv"
    )
    with duckdb.get_connection() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS raw_sales_data AS SELECT * FROM raw_df"
        )
        if not conn.fetchall():
            conn.execute("INSERT INTO raw_sales_data SELECT * FROM raw_df")


@dg.asset(deps=[raw_sales_data])
def clean_sales_data(duckdb: DuckDBResource) -> None:
    with duckdb.get_connection() as conn:
        df = conn.execute("SELECT * FROM raw_sales_data").fetch_df()
        clean_df = df.fillna({"amount": 0.0})
        conn.execute(
            "CREATE TABLE IF NOT EXISTS clean_sales_data AS SELECT * FROM clean_df"
        )
        if not conn.fetchall():
            conn.execute("INSERT INTO clean_sales_data SELECT * FROM clean_df")


@dg.asset(deps=[clean_sales_data])
def sales_summary(duckdb: DuckDBResource) -> None:
    with duckdb.get_connection() as conn:
        df = conn.execute("SELECT * FROM clean_sales_data").fetch_df()
        summary = df.groupby(["owner"])["amount"].sum().reset_index()
        conn.execute(
            "CREATE TABLE IF NOT EXISTS sales_summary AS SELECT * from summary"
        )
        if not conn.fetchall():
            conn.execute("INSERT INTO sales_summary SELECT * from summary")


defs = dg.Definitions(
    assets=[raw_sales_data, clean_sales_data, sales_summary],
    resources={"duckdb": DuckDBResource(database="sales.duckdb", schema="public")},
)

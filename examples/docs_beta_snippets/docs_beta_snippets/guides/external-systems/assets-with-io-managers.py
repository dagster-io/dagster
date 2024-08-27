import pandas as pd
from dagster_duckdb_pandas import DuckDBPandasIOManager

import dagster as dg

raw_sales_data = dg.AssetSpec("raw_sales_data")


@dg.asset
def clean_sales_data(raw_sales_data: pd.DataFrame) -> pd.DataFrame:
    return raw_sales_data.fillna({"amount": 0.0})


@dg.asset
def sales_summary(clean_sales_data: pd.DataFrame) -> pd.DataFrame:
    return clean_sales_data.groupby(["owner"])["amount"].sum().reset_index()


defs = dg.Definitions(
    assets=[clean_sales_data, sales_summary],
    resources={
        "io_manager": DuckDBPandasIOManager(database="sales.duckdb", schema="public")
    },
)

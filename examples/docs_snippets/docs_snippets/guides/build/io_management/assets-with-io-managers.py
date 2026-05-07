import pandas as pd
from dagster_duckdb_pandas import DuckDBPandasIOManager

import dagster as dg


@dg.asset
def raw_sales_data() -> pd.DataFrame:
    return pd.read_csv("https://docs.dagster.io/assets/raw_sales_data.csv")


# highlight-start
@dg.asset
# Load the upstream `raw_sales_data` asset as input & specify the returned data type (`pd.DataFrame`)
def clean_sales_data(raw_sales_data: pd.DataFrame) -> pd.DataFrame:
    # Storing data with an I/O manager requires returning the data
    return raw_sales_data.fillna({"amount": 0.0})
    # highlight-end


@dg.asset
def sales_summary(clean_sales_data: pd.DataFrame) -> pd.DataFrame:
    return clean_sales_data.groupby(["owner"])["amount"].sum().reset_index()

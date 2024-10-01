import pandas as pd
from dagster_duckdb_pandas import DuckDBPandasIOManager

import dagster as dg


@dg.asset
def raw_sales_data() -> pd.DataFrame:
    return pd.read_csv(
        "https://raw.githubusercontent.com/dagster-io/dagster/master/docs/next/public/assets/raw_sales_data.csv"
    )


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


defs = dg.Definitions(
    assets=[raw_sales_data, clean_sales_data, sales_summary],
    # highlight-start
    # Define the I/O manager and pass it to `Definitions`
    resources={
        "io_manager": DuckDBPandasIOManager(database="sales.duckdb", schema="public")
    },
    # highlight-end
)

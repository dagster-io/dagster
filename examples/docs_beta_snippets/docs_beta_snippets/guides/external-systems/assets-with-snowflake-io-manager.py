import pandas as pd
from dagster_snowflake_pandas import SnowflakePandasIOManager

import dagster as dg


@dg.asset
def raw_sales_data() -> pd.DataFrame:
    return pd.read_csv(
        "https://raw.githubusercontent.com/dagster-io/dagster/master/docs/next/public/assets/raw_sales_data.csv"
    )


@dg.asset
def clean_sales_data(raw_sales_data: pd.DataFrame) -> pd.DataFrame:
    return raw_sales_data.fillna({"amount": 0.0})


@dg.asset
def sales_summary(clean_sales_data: pd.DataFrame) -> pd.DataFrame:
    return clean_sales_data.groupby(["owner"])["amount"].sum().reset_index()


defs = dg.Definitions(
    assets=[raw_sales_data, clean_sales_data, sales_summary],
    resources={
        # highlight-start
        # Swap in a Snowflake I/O manager
        "io_manager": SnowflakePandasIOManager(
            database=dg.EnvVar("SNOWFLAKE_DATABASE"),
            account=dg.EnvVar("SNOWFLAKE_ACCOUNT"),
            user=dg.EnvVar("SNOWFLAKE_USER"),
            password=dg.EnvVar("SNOWFLAKE_PASSWORD"),
        )
    },
    # highlight-end
)

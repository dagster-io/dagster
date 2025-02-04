import pandas as pd
from dagster_snowflake_pandas import SnowflakePandasIOManager
from dagster_snowflake_pyspark import SnowflakePySparkIOManager

# spark dataframe
from pyspark.sql import DataFrame as SparkDataFrame

import dagster as dg


@dg.asset
def raw_sales_data() -> pd.DataFrame:
    return pd.read_csv(
        "https://raw.githubusercontent.com/dagster-io/dagster/master/docs/next/public/assets/raw_sales_data.csv"
    )


@dg.asset(
    deps=[raw_sales_data],
    # highlight-start
    # Use the SnowflakePySparkIOManager when loading the input from the upstream asset.
    ins={"raw_sales_data": dg.AssetIn(input_manager_key="snowflake_psyark")},
    # highlight-end
)
def clean_sales_data(raw_sales_data: SparkDataFrame) -> SparkDataFrame:
    return raw_sales_data.fillna({"amount": 0.0})


defs = dg.Definitions(
    assets=[raw_sales_data, clean_sales_data],
    resources={
        # highlight-start
        # Define the SnowflakePySparkIOManager and pass it to `Definitions`
        "snowflake_psyark": SnowflakePySparkIOManager(
            database=dg.EnvVar("SNOWFLAKE_DATABASE"),
            account=dg.EnvVar("SNOWFLAKE_ACCOUNT"),
            user=dg.EnvVar("SNOWFLAKE_USER"),
            password=dg.EnvVar("SNOWFLAKE_PASSWORD"),
        ),
        # highlight-end
        "io_manager": SnowflakePandasIOManager(
            database=dg.EnvVar("SNOWFLAKE_DATABASE"),
            account=dg.EnvVar("SNOWFLAKE_ACCOUNT"),
            user=dg.EnvVar("SNOWFLAKE_USER"),
            password=dg.EnvVar("SNOWFLAKE_PASSWORD"),
        ),
    },
)

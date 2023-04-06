import pandas as pd
from dagster import Definitions, EnvVar, asset
from dagster_snowflake_pandas import SnowflakePandasIOManager


@asset
def my_pydantic_asset() -> pd.DataFrame:
    return pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})


defs = Definitions(
    assets=[my_pydantic_asset],
    resources={
        "io_manager": SnowflakePandasIOManager(
            database="SANDBOX",
            schema="JAMIE",
            account="na94824.us-east-1",
            user="jamie@elementl.com",
            password=EnvVar("SNOWFLAKE_PASSWORD"),
            warehouse="ELEMENTL",
        )
    },
)

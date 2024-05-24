import pandas as pd
from dagster_snowflake_pandas import SnowflakePandasIOManager

from dagster import Definitions, EnvVar, SourceAsset, asset

iris_harvest_data = SourceAsset(key="iris_harvest_data")


@asset
def iris_dataset() -> pd.DataFrame:
    return pd.read_csv(
        "https://docs.dagster.io/assets/iris.csv",
        names=[
            "sepal_length_cm",
            "sepal_width_cm",
            "petal_length_cm",
            "petal_width_cm",
            "species",
        ],
    )


@asset
def iris_cleaned(iris_dataset: pd.DataFrame) -> pd.DataFrame:
    return iris_dataset.dropna().drop_duplicates()


defs = Definitions(
    assets=[iris_dataset, iris_harvest_data, iris_cleaned],
    resources={
        "io_manager": SnowflakePandasIOManager(
            account="abc1234.us-east-1",
            user=EnvVar("SNOWFLAKE_USER"),
            password=EnvVar("SNOWFLAKE_PASSWORD"),
            database="FLOWERS",
            role="writer",
            warehouse="PLANTS",
            schema="IRIS",
        )
    },
)

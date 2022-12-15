import pandas as pd
from dagster_snowflake_pandas import snowflake_pandas_io_manager

from dagster import Definitions, SourceAsset, asset

iris_harvest_data = SourceAsset(key="iris_harvest_data")


@asset
def iris_dataset() -> pd.DataFrame:
    return pd.read_csv(
        "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data",
        names=[
            "Sepal length (cm)",
            "Sepal width (cm)",
            "Petal length (cm)",
            "Petal width (cm)",
            "Species",
        ],
    )


@asset
def iris_cleaned(iris_dataset: pd.DataFrame):
    return iris_dataset.dropna().drop_duplicates()


defs = Definitions(
    assets=[iris_dataset, iris_harvest_data, iris_cleaned],
    resources={
        "io_manager": snowflake_pandas_io_manager.configured(
            {
                "account": "abc1234.us-east-1",
                "user": {"env": "SNOWFLAKE_USER"},
                "password": {"env": "SNOWFLAKE_PASSWORD"},
                "database": "FLOWERS",
                "schema": "IRIS,",
            }
        )
    },
)

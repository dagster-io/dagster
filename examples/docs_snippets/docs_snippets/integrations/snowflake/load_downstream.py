import pandas as pd
from dagster_snowflake_pandas import snowflake_pandas_io_manager

from dagster import asset, repository, with_resources


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


@repository
def flowers_analysis_repository():
    return with_resources(
        [iris_dataset, iris_cleaned],
        resource_defs={
            "io_manager": snowflake_pandas_io_manager.configured(
                {
                    "database": "FLOWERS",
                    "schema": "IRIS",
                    "account": "abc1234.us-east-1",
                    "user": {"env": "SNOWFLAKE_USER"},
                    "password": {"env": "SNOWFLAKE_PASSWORD"},
                }
            )
        },
    )

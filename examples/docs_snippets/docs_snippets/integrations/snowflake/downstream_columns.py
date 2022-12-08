import pandas as pd
from dagster_snowflake_pandas import snowflake_pandas_io_manager

from dagster import AssetIn, asset, repository, with_resources


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


@asset(
    ins={
        "iris_sepal": AssetIn(
            key="iris_dataset",
            metadata={"columns": ["Sepal length (cm)", "Sepal width (cm)"]},
        )
    }
)
def sepal_data(iris_sepal: pd.DataFrame) -> pd.DataFrame:
    iris_sepal["Sepal area (cm2)"] = (
        iris_sepal["Sepal length (cm)"] * iris_sepal["Sepal width (cm)"]
    )
    return iris_sepal


@repository
def flowers_analysis_repository():
    return with_resources(
        [iris_dataset, sepal_data],
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

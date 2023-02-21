import pandas as pd
from dagster_gcp_pandas import bigquery_pandas_io_manager

from dagster import Definitions, SourceAsset, asset

iris_harvest_data = SourceAsset(key="iris_harvest_data")


@asset
def iris_data() -> pd.DataFrame:
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
def iris_cleaned(iris_data: pd.DataFrame):
    return iris_data.dropna().drop_duplicates()


defs = Definitions(
    assets=[iris_data, iris_harvest_data, iris_cleaned],
    resources={
        "io_manager": bigquery_pandas_io_manager.configured(
            {
                "project": "my-gcp-project",
                "location": "us-east5",
                "dataset": "IRIS",
            }
        )
    },
)

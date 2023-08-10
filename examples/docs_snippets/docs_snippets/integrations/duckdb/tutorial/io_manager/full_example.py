import pandas as pd
from dagster_duckdb_pandas import DuckDBPandasIOManager

from dagster import Definitions, SourceAsset, asset

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
def iris_setosa(iris_dataset: pd.DataFrame) -> pd.DataFrame:
    return iris_dataset[iris_dataset["species"] == "Iris-setosa"]


defs = Definitions(
    assets=[iris_dataset, iris_harvest_data, iris_setosa],
    resources={
        "io_manager": DuckDBPandasIOManager(
            database="path/to/my_duckdb_database.duckdb",
            schema="IRIS",
        )
    },
)

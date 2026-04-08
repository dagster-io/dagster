import pandas as pd
from dagster_clickhouse_pandas import ClickhousePandasIOManager

from dagster import Definitions, asset


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
    assets=[iris_dataset, iris_setosa],
    resources={
        "io_manager": ClickhousePandasIOManager(
            host="localhost",
            port=9000,
            database="default",
            schema="iris",
        )
    },
)

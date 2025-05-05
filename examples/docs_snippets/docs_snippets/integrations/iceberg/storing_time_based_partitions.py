import datetime as dt
import random

import pandas as pd
from dagster_iceberg.config import IcebergCatalogConfig
from dagster_iceberg.io_manager.pandas import PandasIcebergIOManager

from dagster import DailyPartitionsDefinition, Definitions, asset

CATALOG_URI = "sqlite:////home/vscode/workspace/.tmp/examples/catalog.db"
CATALOG_WAREHOUSE = "file:///home/vscode/workspace/.tmp/examples/warehouse"

resources = {
    "io_manager": PandasIcebergIOManager(
        name="test",
        config=IcebergCatalogConfig(
            properties={"uri": CATALOG_URI, "warehouse": CATALOG_WAREHOUSE}
        ),
        namespace="dagster",
    )
}


def get_iris_data_for_date(partition: str) -> pd.DataFrame:
    random.seed(876)
    N = 1440
    d = {
        "timestamp": [dt.date.fromisoformat(partition)],
        "species": [
            random.choice(["Iris-setosa", "Iris-virginica", "Iris-versicolor"])
            for _ in range(N)
        ],
        "sepal_length_cm": [random.uniform(0, 1) for _ in range(N)],
        "sepal_width_cm": [random.uniform(0, 1) for _ in range(N)],
        "petal_length_cm": [random.uniform(0, 1) for _ in range(N)],
        "petal_width_cm": [random.uniform(0, 1) for _ in range(N)],
    }
    return pd.DataFrame.from_dict(d)


@asset(
    partitions_def=DailyPartitionsDefinition(start_date="2023-01-01"),
    metadata={"partition_expr": "time"},
)
def iris_data_per_day(context) -> pd.DataFrame:
    partition = context.partition_key

    # get_iris_data_for_date fetches all of the iris data for a given date,
    # the returned dataframe contains a column named 'time' with that stores
    # the time of the row as an integer of seconds since epoch
    return get_iris_data_for_date(partition)


@asset
def iris_cleaned(iris_data_per_day: pd.DataFrame):
    return iris_data_per_day.dropna().drop_duplicates()


defs = Definitions(assets=[iris_data_per_day, iris_cleaned], resources=resources)

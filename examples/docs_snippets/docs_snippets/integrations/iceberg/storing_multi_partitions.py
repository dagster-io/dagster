import datetime as dt
import random

import pandas as pd
from dagster_iceberg.config import IcebergCatalogConfig
from dagster_iceberg.io_manager.pandas import PandasIcebergIOManager

from dagster import (
    DailyPartitionsDefinition,
    Definitions,
    MultiPartitionsDefinition,
    StaticPartitionsDefinition,
    asset,
)

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
    partitions_def=MultiPartitionsDefinition(
        {
            "date": DailyPartitionsDefinition(start_date="2023-01-01"),
            "species": StaticPartitionsDefinition(
                ["Iris-setosa", "Iris-virginica", "Iris-versicolor"]
            ),
        }
    ),
    metadata={"partition_expr": {"date": "time", "species": "species"}},
)
def iris_dataset_partitioned(context) -> pd.DataFrame:
    partition = context.partition_key.keys_by_dimension
    species = partition["species"]
    date = partition["date"]

    # get_iris_data_for_date fetches all of the iris data for a given date,
    # the returned dataframe contains a column named 'time' with that stores
    # the time of the row as an integer of seconds since epoch
    full_df = get_iris_data_for_date(date)

    return full_df[full_df["species"] == species]


@asset
def iris_cleaned(iris_dataset_partitioned: pd.DataFrame):
    return iris_dataset_partitioned.dropna().drop_duplicates()


defs = Definitions(assets=[iris_dataset_partitioned, iris_cleaned], resources=resources)

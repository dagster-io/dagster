import pandas as pd
from dagster_clickhouse_pandas import (
    ClickhousePandasIOManager,  # ty: ignore[unresolved-import]
)

import dagster as dg


@dg.asset
def iris_dataset() -> (
    pd.DataFrame
):  # asset name is the table name; I/O manager `schema` is the ClickHouse database
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


defs = dg.Definitions(
    assets=[iris_dataset],
    resources={
        "io_manager": ClickhousePandasIOManager(
            host="localhost",
            port=9000,
            database="default",
            schema="iris",
        )
    },
)

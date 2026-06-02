import pandas as pd
from dagster_clickhouse import ClickhouseResource  # ty: ignore[unresolved-import]

from dagster import Definitions, asset


@asset
def iris_dataset(clickhouse: ClickhouseResource) -> None:
    iris_df = pd.read_csv(
        "https://docs.dagster.io/assets/iris.csv",
        names=[
            "sepal_length_cm",
            "sepal_width_cm",
            "petal_length_cm",
            "petal_width_cm",
            "species",
        ],
    )

    with clickhouse.get_connection() as client:
        client.execute("CREATE DATABASE IF NOT EXISTS iris")
        client.execute(
            "CREATE TABLE IF NOT EXISTS iris.iris_dataset ("
            " `sepal_length_cm` Float64,"
            " `sepal_width_cm` Float64,"
            " `petal_length_cm` Float64,"
            " `petal_width_cm` Float64,"
            " `species` String"
            ") ENGINE = MergeTree() ORDER BY tuple()"
        )
        if not iris_df.empty:
            client.insert_dataframe(
                "INSERT INTO iris.iris_dataset VALUES",
                iris_df,
                settings={"use_numpy": True},
            )


@asset(deps=[iris_dataset])
def iris_setosa(clickhouse: ClickhouseResource) -> None:
    with clickhouse.get_connection() as client:
        client.execute("DROP TABLE IF EXISTS iris.iris_setosa")
        client.execute(
            "CREATE TABLE iris.iris_setosa ENGINE = MergeTree() ORDER BY tuple() AS"
            " SELECT * FROM iris.iris_dataset WHERE species = 'Iris-setosa'"
        )


defs = Definitions(
    assets=[iris_dataset, iris_setosa],
    resources={
        "clickhouse": ClickhouseResource(
            host="localhost",
            port=9000,
        )
    },
)

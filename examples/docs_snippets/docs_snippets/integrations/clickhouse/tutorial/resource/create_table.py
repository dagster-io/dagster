# start_example
import pandas as pd
from dagster_clickhouse import ClickhouseResource

from dagster import asset


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


# end_example

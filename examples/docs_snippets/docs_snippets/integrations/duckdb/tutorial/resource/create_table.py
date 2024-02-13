# start_example
import pandas as pd
from dagster_duckdb import DuckDBResource

from dagster import asset


@asset
def iris_dataset(duckdb: DuckDBResource) -> None:
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

    with duckdb.get_connection() as conn:
        conn.execute("CREATE TABLE iris.iris_dataset AS SELECT * FROM iris_df")


# end_example

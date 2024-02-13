import pandas as pd
from dagster_duckdb import DuckDBResource

from dagster import Definitions, SourceAsset, asset

iris_harvest_data = SourceAsset(key="iris_harvest_data")


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


@asset(deps=[iris_dataset])
def iris_setosa(duckdb: DuckDBResource) -> None:
    with duckdb.get_connection() as conn:
        conn.execute(
            "CREATE TABLE iris.iris_setosa AS SELECT * FROM iris.iris_dataset WHERE"
            " species = 'Iris-setosa'"
        )


defs = Definitions(
    assets=[iris_dataset],
    resources={
        "duckdb": DuckDBResource(
            database="path/to/my_duckdb_database.duckdb",
        )
    },
)

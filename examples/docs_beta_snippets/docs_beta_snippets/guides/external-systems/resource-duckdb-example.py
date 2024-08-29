import pandas as pd
from dagster_duckdb import DuckDBResource

import dagster as dg


# highlight-start
# An asset that uses a DuckDb resource called iris_db
# Note the parameter name `iris_db` must match the resource defined later
@dg.asset
def iris_dataset(iris_db: DuckDBResource) -> None:
    # highlight-end
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

    # highlight-start
    with iris_db.get_connection() as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS iris")
        conn.execute("CREATE TABLE iris.iris_dataset AS SELECT * FROM iris_df")
    # highlight-end


# Another asset that uses the iris_db resource
@dg.asset(deps=[iris_dataset])
def iris_setosa(iris_db: DuckDBResource) -> None:
    with iris_db.get_connection() as conn:
        conn.execute(
            "CREATE TABLE iris.iris_setosa AS SELECT * FROM iris.iris_dataset WHERE"
            " species = 'Iris-setosa'"
        )


defs = dg.Definitions(
    assets=[iris_dataset, iris_setosa],
    resources={
        # highlight-start
        # This defines a DuckDB resource called iris_db
        "iris_db": DuckDBResource(
            database="/tmp/iris_dataset.duckdb",
        )
        # highlight-end
    },
)

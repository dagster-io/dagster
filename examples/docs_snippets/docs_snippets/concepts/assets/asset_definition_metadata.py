# start
from dagster_duckdb import DuckDBResource
from integrations.duckdb.tutorial.resource.create_table import (
    iris_dataset,
)

from dagster import asset


@asset(
    deps=[iris_dataset],
    metadata={
        "Expected columns": "sepal_length_cm, sepal_width_cm, petal_length_cm, petal_width_cm, species"
    },
)
def small_petals(duckdb: DuckDBResource) -> None:
    with duckdb.get_connection() as conn:
        conn.execute(
            "CREATE TABLE iris.small_petals AS SELECT * FROM iris.iris_dataset WHERE"
            " 'petal_length_cm' < 1 AND 'petal_width_cm' < 1"
        )


# end

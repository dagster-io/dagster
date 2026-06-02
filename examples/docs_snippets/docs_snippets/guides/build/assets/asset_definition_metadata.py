# ruff: noqa

from docs_snippets.integrations.duckdb.tutorial.resource.create_table import (
    iris_dataset,
)

# start
from dagster_duckdb import DuckDBResource

from dagster import asset

# ... other assets


@asset(
    deps=[iris_dataset],
    metadata={"dataset_name": "iris.small_petals"},
)
def small_petals(duckdb: DuckDBResource) -> None:
    with duckdb.get_connection() as conn:
        conn.execute(
            "CREATE TABLE iris.small_petals AS SELECT * FROM iris.iris_dataset WHERE"
            " 'petal_length_cm' < 1 AND 'petal_width_cm' < 1"
        )


# end

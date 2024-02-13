from ..tutorial.resource.create_table import iris_dataset  # noqa: I001


# start
from dagster_duckdb import DuckDBResource

from dagster import asset

# this example executes a query against the iris_dataset table created in Step 2 of the
# Using Dagster with DuckDB tutorial


@asset(deps=[iris_dataset])
def small_petals(duckdb: DuckDBResource) -> None:
    with duckdb.get_connection() as conn:  # conn is a DuckDBPyConnection
        conn.execute(
            "CREATE TABLE iris.small_petals AS SELECT * FROM iris.iris_dataset WHERE"
            " 'petal_length_cm' < 1 AND 'petal_width_cm' < 1"
        )


# end

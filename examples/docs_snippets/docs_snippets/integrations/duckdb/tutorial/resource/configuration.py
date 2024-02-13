from dagster import asset


@asset
def iris_dataset():
    return None


# start_example

from dagster_duckdb import DuckDBResource

from dagster import Definitions

defs = Definitions(
    assets=[iris_dataset],
    resources={
        "duckdb": DuckDBResource(
            database="path/to/my_duckdb_database.duckdb",  # required
        )
    },
)


# end_example

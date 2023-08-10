from dagster import asset


@asset
def iris_dataset():
    return None


# start_example

from dagster_duckdb_pandas import DuckDBPandasIOManager

from dagster import Definitions

defs = Definitions(
    assets=[iris_dataset],
    resources={
        "io_manager": DuckDBPandasIOManager(
            database="path/to/my_duckdb_database.duckdb",  # required
            schema="IRIS",  # optional, defaults to PUBLIC
        )
    },
)


# end_example

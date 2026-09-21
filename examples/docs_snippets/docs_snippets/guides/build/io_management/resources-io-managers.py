from dagster_duckdb_pandas import DuckDBPandasIOManager

import dagster as dg


@dg.definitions
def resources():
    return dg.Definitions(
        # highlight-start
        # Define the I/O manager and pass it to `Definitions`
        resources={
            "io_manager": DuckDBPandasIOManager(
                database="sales.duckdb", schema="public"
            )
        }
        # highlight-end
    )

from dagster_duckdb_pandas import DuckDBResource

import dagster as dg


@dg.definitions
def resources():
    return dg.Definitions(
        resources={"duckdb": DuckDBResource(database="sales.duckdb", schema="public")}
    )

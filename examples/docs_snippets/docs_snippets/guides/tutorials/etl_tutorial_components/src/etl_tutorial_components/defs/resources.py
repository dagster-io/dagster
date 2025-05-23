from dagster_duckdb import DuckDBResource

import dagster as dg

database_resource = DuckDBResource(database="duckdb:///var/tmp/duckdb.db")

defs = dg.Definitions(
    resources={
        "duckdb": database_resource,
    }
)

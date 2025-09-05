import dagster as dg
from dagster_duckdb import DuckDBResource

database_resource = DuckDBResource(database="/tmp/jaffle_platform.duckdb")


@dg.definitions
def resources():
    return dg.Definitions(
        resources={
            "duckdb": database_resource,
        }
    )

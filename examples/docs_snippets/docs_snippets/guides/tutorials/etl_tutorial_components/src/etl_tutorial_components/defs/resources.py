from dagster_duckdb import DuckDBResource
from dagster_sling import SlingConnectionResource, SlingResource


import dagster as dg

database_resource = DuckDBResource(database="duckdb:///var/tmp/duckdb.db")

source = SlingConnectionResource(
    name="LOCAL",
    type="local",
)

destination = SlingConnectionResource(
    name="MY_DUCKDB",
    type="duckdb",
    connection_string="duckdb:///var/tmp/duckdb.db",
)


defs = dg.Definitions(
    resources={
        "duckdb": database_resource,
        "sling": SlingResource(
            connections=[
                source,
                destination,
            ]
        ),
    }
)

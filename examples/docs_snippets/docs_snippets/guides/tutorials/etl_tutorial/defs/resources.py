from dagster_duckdb import DuckDBResource
from dagster_sling import SlingConnectionResource, SlingResource

import dagster as dg

destination = SlingConnectionResource(
    name="MY_DUCKDB",
    type="duckdb",
    connection_string="duckdb:///var/tmp/duckdb.db",
)

sling = SlingResource(
    connections=[
        destination,
    ]
)

database_resource = DuckDBResource(database="duckdb:///var/tmp/duckdb.db")

defs = dg.Definitions(
    resources={
        "duckdb": database_resource,
        "sling": sling,
    }
)

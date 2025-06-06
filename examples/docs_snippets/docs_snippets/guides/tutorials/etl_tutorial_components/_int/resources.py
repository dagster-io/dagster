# start_sling_resource
from dagster_sling import SlingConnectionResource, SlingResource

import dagster as dg

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
        "sling": SlingResource(
            connections=[
                source,
                destination,
            ]
        ),
    }
)


# end_sling_resource


# start_dbt_resource
from dagster_sling import SlingConnectionResource, SlingResource
from etl_tutorial_components.defs.dbt_assets import dbt_resource

import dagster as dg

...


defs = dg.Definitions(
    resources={
        "sling": SlingResource(
            connections=[
                source,
                destination,
            ]
        ),
        "dbt": dbt_resource,  # dbt resource
    }
)

# end_dbt_resource


# start_duckdb_resource
from dagster_duckdb import DuckDBResource
from dagster_sling import SlingConnectionResource, SlingResource
from etl_tutorial_components.defs.dbt_assets import dbt_resource

import dagster as dg

database_resource = DuckDBResource(database="duckdb:///var/tmp/duckdb.db")

...


defs = dg.Definitions(
    resources={
        "duckdb": database_resource,  # duckdb resource
        "sling": SlingResource(
            connections=[
                source,
                destination,
            ]
        ),
        "dbt": dbt_resource,
    }
)


# end_duckdb_resource

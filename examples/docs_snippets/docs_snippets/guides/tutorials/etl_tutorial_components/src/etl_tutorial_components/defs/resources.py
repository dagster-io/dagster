from dagster_duckdb import DuckDBResource
from dagster_evidence import EvidenceResource
from dagster_sling import SlingConnectionResource, SlingResource

import dagster as dg
from etl_tutorial_components.defs.dbt_assets import dbt_resource


# start_database_resource
database_resource = DuckDBResource(database="duckdb:///var/tmp/duckdb.db")

# end_database_resource

source = SlingConnectionResource(
    name="LOCAL",
    type="local",
)

destination = SlingConnectionResource(
    name="MY_DUCKDB",
    type="duckdb",
    connection_string="duckdb:///var/tmp/duckdb.db",
)

evidence_resource = EvidenceResource(
    project_path="../../../../jaffle_dashboard",
    deploy_command='echo "Dashboard built at $EVIDENCE_BUILD_PATH"',
)


# start_resources_definitions
@dg.definitions
def resources():
    return dg.Definitions(
        resources={
            "duckdb": database_resource,
            "sling": SlingResource(
                connections=[
                    source,
                    destination,
                ]
            ),
            "evidence": evidence_resource,
            "dbt": dbt_resource,
        }
    )
# end_resources_definitions
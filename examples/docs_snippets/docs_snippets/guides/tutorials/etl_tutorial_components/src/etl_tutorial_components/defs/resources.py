from dagster_duckdb import DuckDBResource
from dagster_sling import SlingConnectionResource, SlingResource
from dagster_evidence import EvidenceResource


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

evidence_resource = EvidenceResource(
    project_path="../../../../jaffle_dashboard",
    deploy_command='echo "Dashboard built at $EVIDENCE_BUILD_PATH"',
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
        "evidence": evidence_resource
    }
)

# pyright: reportCallIssue=none
from dagster_sling import SlingConnectionResource, SlingResource

from dagster import EnvVar

sling_resource = SlingResource(
    connections=[
        # Using a connection string from an environment variable
        SlingConnectionResource(
            name="MY_POSTGRES",
            type="postgres",
            connection_string=EnvVar("POSTGRES_CONNECTION_STRING"),
        ),
        # Using a hard-coded connection string
        SlingConnectionResource(
            name="MY_DUCKDB",
            type="duckdb",
            connection_string="duckdb:///var/tmp/duckdb.db",
        ),
        # Using a keyword-argument constructor
        SlingConnectionResource(
            name="MY_SNOWFLAKE",
            type="snowflake",
            host=EnvVar("SNOWFLAKE_HOST"),
            user=EnvVar("SNOWFLAKE_USER"),
            role="REPORTING",
        ),
    ]
)

# pyright: reportCallIssue=none
# pyright: reportOptionalMemberAccess=none

from dagster_sling import SlingConnectionResource, SlingResource, sling_assets

from dagster import EnvVar

source = SlingConnectionResource(
    name="MY_PG",
    type="postgres",
    host="localhost",
    port=5432,
    database="my_database",
    user="my_user",
    password=EnvVar("PG_PASS"),
)

target = SlingConnectionResource(
    name="MY_SF",
    type="snowflake",
    host="hostname.snowflake",
    user="username",
    database="database",
    password=EnvVar("SF_PASSWORD"),
    role="role",
)

sling = SlingResource(
    connections=[
        source,
        target,
    ]
)
replication_config = {
    "SOURCE": "MY_PG",
    "TARGET": "MY_SF",
    "defaults": {"mode": "full-refresh", "object": "{stream_schema}_{stream_table}"},
    "streams": {
        "public.accounts": None,
        "public.users": None,
        "public.finance_departments": {"object": "departments"},
    },
}


@sling_assets(replication_config=replication_config)
def my_assets(context, sling: SlingResource):
    yield from sling.replicate(context=context)

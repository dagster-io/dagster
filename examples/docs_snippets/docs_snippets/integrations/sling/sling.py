from dagster_sling import SlingConnectionResource, SlingResource, sling_assets

import dagster as dg

source = SlingConnectionResource(
    name="MY_PG",
    type="postgres",
    host="localhost",
    port=5432,
    database="my_database",
    user="my_user",
    password=dg.EnvVar("PG_PASS"),
)

target = SlingConnectionResource(
    name="MY_SF",
    type="snowflake",
    host="hostname.snowflake",
    user="username",
    database="database",
    password=dg.EnvVar("SF_PASSWORD"),
    role="role",
)


@sling_assets(
    replication_config={
        "source": "MY_PG",
        "target": "MY_SF",
        "defaults": {
            "mode": "full-refresh",
            "object": "{stream_schema}_{stream_table}",
        },
        "streams": {
            "public.accounts": None,
            "public.users": None,
            "public.finance_departments": {"object": "departments"},
        },
    }
)
def my_sling_assets(context, sling: SlingResource):
    yield from sling.replicate(context=context)


defs = dg.Definitions(
    assets=[my_sling_assets],
    resources={
        "sling": SlingResource(
            connections=[
                source,
                target,
            ]
        )
    },
)

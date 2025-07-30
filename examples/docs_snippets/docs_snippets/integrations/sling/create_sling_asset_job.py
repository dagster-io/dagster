from dagster_sling import SlingConnectionResource, SlingResource, sling_assets

import dagster as dg

source = SlingConnectionResource(
    name="MY_PG",
    type="postgres",
    host="localhost",  # type: ignore
    port=5432,  # type: ignore
    database="my_database",  # type: ignore
    user="my_user",  # type: ignore
    password=dg.EnvVar("PG_PASS"),  # type: ignore
)

target = SlingConnectionResource(
    name="MY_SF",
    type="snowflake",
    host="hostname.snowflake",  # type: ignore
    user="username",  # type: ignore
    database="database",  # type: ignore
    password=dg.EnvVar("SF_PASSWORD"),  # type: ignore
    role="role",  # type: ignore
)

replication_config = {
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


@sling_assets(
    replication_config=replication_config,
)
def my_sling_assets(context, sling: SlingResource):
    yield from sling.replicate(context=context)


# start_sling_job
my_sling_assets_job = dg.define_asset_job(
    name="my_sling_assets_job",
    selection=[my_sling_assets],
)

defs = dg.Definitions(
    assets=[my_sling_assets],
    jobs=[my_sling_assets_job],
    resources={
        "sling": SlingResource(
            connections=[
                source,
                target,
            ]
        )
    },
)
# end_sling_job

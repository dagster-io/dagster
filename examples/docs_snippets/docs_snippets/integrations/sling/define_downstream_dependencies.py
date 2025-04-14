from collections.abc import Mapping
from typing import Any

from dagster_sling import (
    DagsterSlingTranslator,
    SlingConnectionResource,
    SlingResource,
    sling_assets,
)

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


# start_downstream_asset
from dagster_sling.asset_decorator import get_streams_from_replication


@sling_assets(
    replication_config=replication_config,
)
def my_sling_assets(context, sling: SlingResource):
    yield from sling.replicate(context=context)


my_sling_stream_asset_key = next(
    iter(
        [
            DagsterSlingTranslator().get_asset_spec(stream_definition=stream)
            for stream in get_streams_from_replication(replication_config)
            if stream["name"] == "my_sling_stream"
        ]
    )
)


@dg.asset(deps=[my_sling_stream_asset_key])
def my_downstream_asset(): ...


# end_downstream_asset

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

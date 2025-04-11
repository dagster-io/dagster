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


# start_upstream_asset
class CustomDagsterSlingTranslator(DagsterSlingTranslator):
    def get_asset_spec(self, stream_definition: Mapping[str, Any]) -> dg.AssetSpec:
        """Overrides asset spec to override upstream asset key to be a single source asset."""
        # We create the default asset spec using super()
        default_spec = super().get_asset_spec(stream_definition)
        # We set an upstream dependency for our assets
        return default_spec.replace_attributes(
            deps=[dg.AssetKey("common_upstream_sling_dependency")],
        )


@sling_assets(
    replication_config=replication_config,
    dagster_sling_translator=CustomDagsterSlingTranslator(),
)
def my_sling_assets(context, sling: SlingResource):
    yield from sling.replicate(context=context)


# end_upstream_asset

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

# pyright: reportGeneralTypeIssues=none
# pyright: reportOptionalMemberAccess=none

import os

from dagster_embedded_elt.sling import (
    SlingMode,
    SlingResource,
    SlingSourceConnection,
    SlingTargetConnection,
    build_sling_asset,
)

from dagster import AssetSpec

source = SlingSourceConnection(
    type="postgres",
    host="localhost",
    port=5432,
    database="my_database",
    user="my_user",
    password=os.getenv("PG_PASS"),
)

target = SlingTargetConnection(
    type="snowflake",
    host="hostname.snowflake",
    user="username",
    database="database",
    password=os.getenv("SF_PASSWORD"),
    role="role",
)

sling = SlingResource(source_connection=source, target_connection=target)

asset_def = build_sling_asset(
    asset_spec=AssetSpec("my_asset_name"),
    source_stream="public.my_table",
    target_object="marts.my_table",
    mode=SlingMode.INCREMENTAL,
    primary_key="id",
)

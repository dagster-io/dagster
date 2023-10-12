# pyright: reportGeneralTypeIssues=none
# pyright: reportOptionalMemberAccess=none

import os

from dagster_embedded_elt.sling import (
    SlingResource,
    SlingSourceConnection,
    SlingTargetConnection,
    build_sling_asset,
)

from dagster import AssetSpec

target = SlingTargetConnection(
    type="snowflake",
    host="hostname.snowflake",
    user="username",
    database="database",
    password=os.getenv("SF_PASSWORD"),
    role="role",
)


# start_storage_config
source = SlingSourceConnection(
    type="s3",
    bucket="sling-bucket",
    access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

sling = SlingResource(source_connection=source, target_connection=target)

asset_def = build_sling_asset(
    asset_spec=AssetSpec("my_asset_name"),
    source_stream="s3://my-bucket/my_file.parquet",
    target_object="marts.my_table",
    primary_key="id",
)

# end_storage_config

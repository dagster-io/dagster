from dagster import Definitions, EnvVar, asset
from dagster_embedded_elt.sling import (
    AssetSpec,
    SlingMode,
    SlingResource,
    SlingSourceConnection,
    SlingTargetConnection,
    build_sling_asset,
)

# Step 1: Configure Connections
sling_resource = SlingResource(
    source_connection=SlingSourceConnection(
        type="postgres", connection_string=EnvVar("POSTGRES_CONNECTION_STRING")
    ),
    target_connection=SlingTargetConnection(
        type="snowflake", connection_string=EnvVar("SNOWFLAKE_CONNECTION_STRING")
    ),
)


# Step 2: Define the ELT Asset
@asset
def postgres_to_snowflake(sling):
    asset_def = build_sling_asset(
        asset_spec=AssetSpec("postgres_to_snowflake"),
        source_stream="public.source_table",
        target_object="target_schema.target_table",
        mode=SlingMode.INCREMENTAL,
        primary_key="id",
    )
    return asset_def


# Step 3: Execute the ELT Process
defs = Definitions(assets=[postgres_to_snowflake], resources={"sling": sling_resource})

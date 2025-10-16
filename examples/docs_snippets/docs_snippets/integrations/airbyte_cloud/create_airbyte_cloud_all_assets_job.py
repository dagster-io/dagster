from dagster_airbyte import AirbyteCloudWorkspace, build_airbyte_assets_definitions

import dagster as dg

airbyte_workspace = AirbyteCloudWorkspace(
    workspace_id=dg.EnvVar("AIRBYTE_CLOUD_WORKSPACE_ID"),
    client_id=dg.EnvVar("AIRBYTE_CLOUD_CLIENT_ID"),
    client_secret=dg.EnvVar("AIRBYTE_CLOUD_CLIENT_SECRET"),
)

all_airbyte_assets = build_airbyte_assets_definitions(workspace=airbyte_workspace)

all_airbyte_assets_job = dg.define_asset_job(
    name="all_airbyte_assets_job",
    selection=all_airbyte_assets,
)

defs = dg.Definitions(
    assets=all_airbyte_assets,
    jobs=[all_airbyte_assets_job],
    resources={"airbyte": airbyte_workspace},
)

from dagster_airbyte import AirbyteCloudWorkspace, build_airbyte_assets_definitions

import dagster as dg

airbyte_workspace = AirbyteCloudWorkspace(
    workspace_id=dg.EnvVar("AIRBYTE_CLOUD_WORKSPACE_ID"),
    client_id=dg.EnvVar("AIRBYTE_CLOUD_CLIENT_ID"),
    client_secret=dg.EnvVar("AIRBYTE_CLOUD_CLIENT_SECRET"),
)

all_airbyte_assets = build_airbyte_assets_definitions(workspace=airbyte_workspace)

defs = dg.Definitions(
    assets=all_airbyte_assets,
    resources={"airbyte": airbyte_workspace},
)

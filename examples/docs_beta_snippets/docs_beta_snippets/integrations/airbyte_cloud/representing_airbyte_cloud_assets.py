from dagster_airbyte import AirbyteCloudWorkspace, load_airbyte_cloud_asset_specs

import dagster as dg

airbyte_workspace = AirbyteCloudWorkspace(
    workspace_id=dg.EnvVar("AIRBYTE_CLOUD_WORKSPACE_ID"),
    client_id=dg.EnvVar("AIRBYTE_CLOUD_CLIENT_ID"),
    client_secret=dg.EnvVar("AIRBYTE_CLOUD_CLIENT_SECRET"),
)


airbyte_cloud_specs = load_airbyte_cloud_asset_specs(airbyte_workspace)
defs = dg.Definitions(assets=airbyte_cloud_specs)

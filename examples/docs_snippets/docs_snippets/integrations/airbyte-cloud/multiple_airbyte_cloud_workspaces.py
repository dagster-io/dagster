from dagster_airbyte import AirbyteCloudWorkspace, load_airbyte_cloud_asset_specs

import dagster as dg

sales_airbyte_workspace = AirbyteCloudWorkspace(
    workspace_id=dg.EnvVar("AIRBYTE_CLOUD_SALES_WORKSPACE_ID"),
    client_id=dg.EnvVar("AIRBYTE_CLOUD_SALES_CLIENT_ID"),
    client_secret=dg.EnvVar("AIRBYTE_CLOUD_SALES_CLIENT_SECRET"),
)

marketing_airbyte_workspace = AirbyteCloudWorkspace(
    workspace_id=dg.EnvVar("AIRBYTE_CLOUD_MARKETING_WORKSPACE_ID"),
    client_id=dg.EnvVar("AIRBYTE_CLOUD_MARKETING_CLIENT_ID"),
    client_secret=dg.EnvVar("AIRBYTE_CLOUD_MARKETING_CLIENT_SECRET"),
)

sales_airbyte_cloud_specs = load_airbyte_cloud_asset_specs(
    workspace=sales_airbyte_workspace
)
marketing_airbyte_cloud_specs = load_airbyte_cloud_asset_specs(
    workspace=marketing_airbyte_workspace
)

# Merge the specs into a single set of definitions
defs = dg.Definitions(
    assets=[*sales_airbyte_cloud_specs, *marketing_airbyte_cloud_specs],
)

from dagster_powerbi import (
    PowerBIServicePrincipal,
    PowerBIToken,
    PowerBIWorkspace,
    load_powerbi_asset_specs,
)

import dagster as dg

# Connect using a service principal
power_bi_workspace = PowerBIWorkspace(
    credentials=PowerBIServicePrincipal(
        client_id=dg.EnvVar("POWER_BI_CLIENT_ID"),
        client_secret=dg.EnvVar("POWER_BI_CLIENT_SECRET"),
        tenant_id=dg.EnvVar("POWER_BI_TENANT_ID"),
    ),
    workspace_id=dg.EnvVar("POWER_BI_WORKSPACE_ID"),
)

# Alternatively, connect directly using an API access token
power_bi_workspace = PowerBIWorkspace(
    credentials=PowerBIToken(api_token=dg.EnvVar("POWER_BI_API_TOKEN")),
    workspace_id=dg.EnvVar("POWER_BI_WORKSPACE_ID"),
)

power_bi_specs = load_powerbi_asset_specs(power_bi_workspace)
defs = dg.Definitions(
    assets=[*power_bi_specs], resources={"power_bi": power_bi_workspace}
)

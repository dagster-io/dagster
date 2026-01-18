from dagster_powerbi import (
    PowerBIServicePrincipal,
    PowerBIWorkspace,
    load_powerbi_asset_specs,
)

import dagster as dg

credentials = PowerBIServicePrincipal(
    client_id=dg.EnvVar("POWER_BI_CLIENT_ID"),
    client_secret=dg.EnvVar("POWER_BI_CLIENT_SECRET"),
    tenant_id=dg.EnvVar("POWER_BI_TENANT_ID"),
)

sales_team_workspace = PowerBIWorkspace(
    credentials=credentials,
    workspace_id="726c94ff-c408-4f43-8edf-61fbfa1753c7",
)

marketing_team_workspace = PowerBIWorkspace(
    credentials=credentials,
    workspace_id="8b7f815d-4e64-40dd-993c-cfa4fb12edee",
)

sales_team_specs = load_powerbi_asset_specs(sales_team_workspace)
marketing_team_specs = load_powerbi_asset_specs(marketing_team_workspace)

# Merge the specs into a single set of definitions
defs = dg.Definitions(
    assets=[*sales_team_specs, *marketing_team_specs],
    resources={
        "marketing_power_bi": marketing_team_workspace,
        "sales_power_bi": sales_team_workspace,
    },
)

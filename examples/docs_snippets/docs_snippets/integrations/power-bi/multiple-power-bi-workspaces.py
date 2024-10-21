from dagster_powerbi import PowerBIServicePrincipal, PowerBIWorkspace

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

# We use Definitions.merge to combine the definitions from both workspaces
# into a single set of definitions to load
defs = dg.Definitions.merge(
    sales_team_workspace.build_defs(),
    marketing_team_workspace.build_defs(),
)

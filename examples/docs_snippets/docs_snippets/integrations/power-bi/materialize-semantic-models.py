from dagster_powerbi import (
    PowerBIServicePrincipal,
    PowerBIWorkspace,
    build_semantic_model_refresh_asset_definition,
    load_powerbi_asset_specs,
)

import dagster as dg

power_bi_workspace = PowerBIWorkspace(
    credentials=PowerBIServicePrincipal(
        client_id=dg.EnvVar("POWER_BI_CLIENT_ID"),
        client_secret=dg.EnvVar("POWER_BI_CLIENT_SECRET"),
        tenant_id=dg.EnvVar("POWER_BI_TENANT_ID"),
    ),
    workspace_id=dg.EnvVar("POWER_BI_WORKSPACE_ID"),
)

# Load Power BI asset specs, and use the asset definition builder to
# construct a semantic model refresh definition for each semantic model
power_bi_assets = [
    build_semantic_model_refresh_asset_definition(resource_key="power_bi", spec=spec)
    if spec.tags.get("dagster-powerbi/asset_type") == "semantic_model"
    else spec
    for spec in load_powerbi_asset_specs(power_bi_workspace)
]
defs = dg.Definitions(
    assets=[*power_bi_assets], resources={"power_bi": power_bi_workspace}
)

from dagster_powerbi import PowerBIServicePrincipal, PowerBIWorkspace
from dagster_powerbi.translator import PowerBIContentData

from dagster import EnvVar
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec

resource = PowerBIWorkspace(
    credentials=PowerBIServicePrincipal(
        client_id=EnvVar("POWER_BI_CLIENT_ID"),
        client_secret=EnvVar("POWER_BI_CLIENT_SECRET"),
        tenant_id=EnvVar("POWER_BI_TENANT_ID"),
    ),
    workspace_id=EnvVar("POWER_BI_WORKSPACE_ID"),
)


def customize_powerbi_asset(spec: AssetSpec) -> AssetSpec:
    # We prefix all dashboard asset keys with "powerbi-dashboard" for
    # organizational purposes
    key = spec.key
    if spec.tags["dagster-powerbi/asset_type"] == "dashboard":
        key = key.with_prefix("powerbi-dashboard")

    return spec._replace(key=key, owners="my_team")


defs = resource.build_defs().map_asset_specs(customize_powerbi_asset)

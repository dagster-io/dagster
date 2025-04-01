from dagster_powerbi import (
    DagsterPowerBITranslator,
    PowerBIServicePrincipal,
    PowerBIWorkspace,
    load_powerbi_asset_specs,
)
from dagster_powerbi.translator import PowerBIContentType, PowerBITranslatorData

import dagster as dg

power_bi_workspace = PowerBIWorkspace(
    credentials=PowerBIServicePrincipal(
        client_id=dg.EnvVar("POWER_BI_CLIENT_ID"),
        client_secret=dg.EnvVar("POWER_BI_CLIENT_SECRET"),
        tenant_id=dg.EnvVar("POWER_BI_TENANT_ID"),
    ),
    workspace_id=dg.EnvVar("POWER_BI_WORKSPACE_ID"),
)


# A translator class lets us customize properties of the built
# Power BI assets, such as the owners or asset key
class MyCustomPowerBITranslator(DagsterPowerBITranslator):
    def get_asset_spec(self, data: PowerBITranslatorData) -> dg.AssetSpec:
        # We create the default asset spec using super()
        default_spec = super().get_asset_spec(data)
        # We customize the team owner tag for all assets,
        # and we customize the asset key prefix only for dashboards.
        return default_spec.replace_attributes(
            key=(
                default_spec.key.with_prefix("prefix")
                if data.content_type == PowerBIContentType.DASHBOARD
                else default_spec.key
            ),
            owners=["team:my_team"],
        )


power_bi_specs = load_powerbi_asset_specs(
    power_bi_workspace, dagster_powerbi_translator=MyCustomPowerBITranslator()
)
defs = dg.Definitions(
    assets=[*power_bi_specs], resources={"power_bi": power_bi_workspace}
)

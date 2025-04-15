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


# start_upstream_asset
class MyCustomPowerBITranslator(DagsterPowerBITranslator):
    def get_asset_spec(self, data: PowerBITranslatorData) -> dg.AssetSpec:
        # We create the default asset spec using super()
        default_spec = super().get_asset_spec(data)
        # We customize upstream dependencies for the PowerBI semantic model named `my_powerbi_semantic_model`
        return default_spec.replace_attributes(
            deps=["my_upstream_asset"]
            if data.content_type == PowerBIContentType.SEMANTIC_MODEL
            and data.properties.get("name") == "my_powerbi_semantic_model"
            else ...
        )


power_bi_specs = load_powerbi_asset_specs(
    power_bi_workspace, dagster_powerbi_translator=MyCustomPowerBITranslator()
)
# end_upstream_asset

defs = dg.Definitions(
    assets=[*power_bi_specs], resources={"power_bi": power_bi_workspace}
)

import dagster as dg
from dagster_powerbi import (
    DagsterPowerBITranslator,
    PowerBIServicePrincipal,
    PowerBIWorkspace,
    load_powerbi_asset_specs,
)
from dagster_powerbi.translator import PowerBITranslatorData

# start_powerbi
power_bi_workspace = PowerBIWorkspace(
    credentials=PowerBIServicePrincipal(
        client_id=dg.EnvVar("AZURE_POWERBI_CLIENT_ID"),
        client_secret=dg.EnvVar("AZURE_POWERBI_CLIENT_SECRET"),
        tenant_id=dg.EnvVar("AZURE_POWERBI_TENANT_ID"),
    ),
    workspace_id=dg.EnvVar("AZURE_POWERBI_WORKSPACE_ID"),
)
# end_powerbi


# start_dbt
class CustomDagsterPowerBITranslator(DagsterPowerBITranslator):
    def get_report_spec(self, data: PowerBITranslatorData) -> dg.AssetSpec:
        return (
            super()
            .get_report_spec(data)
            .replace_attributes(
                group_name="reporting",
            )
        )

    def get_semantic_model_spec(self, data: PowerBITranslatorData) -> dg.AssetSpec:
        upsteam_table_deps = [
            dg.AssetKey(table.get("name")) for table in data.properties.get("tables", [])
        ]
        return (
            super()
            .get_semantic_model_spec(data)
            .replace_attributes(
                group_name="reporting",
                deps=upsteam_table_deps,
            )
        )


# end_dbt

# start_def
power_bi_specs = load_powerbi_asset_specs(
    power_bi_workspace,
    dagster_powerbi_translator=CustomDagsterPowerBITranslator(),
)


# end_def

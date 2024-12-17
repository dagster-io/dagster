import dagster as dg
from dagster_powerbi import (
    DagsterPowerBITranslator,
    PowerBIServicePrincipal,
    PowerBIWorkspace,
    load_powerbi_asset_specs,
)
from dagster_powerbi.translator import PowerBIContentData

power_bi_workspace = PowerBIWorkspace(
    credentials=PowerBIServicePrincipal(
        client_id=dg.EnvVar("AZURE_POWERBI_CLIENT_ID"),
        client_secret=dg.EnvVar("AZURE_POWERBI_CLIENT_SECRET"),
        tenant_id=dg.EnvVar("AZURE_POWERBI_TENANT_ID"),
    ),
    workspace_id=dg.EnvVar("AZURE_POWERBI_WORKSPACE_ID"),
)


def _construct_report_url(report_id: str) -> str:
    workspace_id = dg.EnvVar("AZURE_POWERBI_WORKSPACE_ID").get_value()
    return f"https://app.powerbi.com/groups/{workspace_id}/reports/{report_id}"


def _construct_semantic_model_url(model_id: str) -> str:
    workspace_id = dg.EnvVar("AZURE_POWERBI_WORKSPACE_ID").get_value()
    return f"https://app.powerbi.com/groups/{workspace_id}/datasets/{model_id}/details"


class CustomDagsterPowerBITranslator(DagsterPowerBITranslator):
    def get_report_spec(self, data: PowerBIContentData) -> dg.AssetSpec:
        return (
            super()
            .get_report_spec(data)
            .replace_attributes(
                group_name="reporting",
                description=f"Report URL: {_construct_report_url(data.properties['id'])}",
            )
        )

    def get_semantic_model_spec(self, data: PowerBIContentData) -> dg.AssetSpec:
        upsteam_table_deps = [
            dg.AssetKey(table.get("name")) for table in data.properties.get("tables", [])
        ]
        return (
            super()
            .get_semantic_model_spec(data)
            .replace_attributes(
                group_name="reporting",
                description=f"Semantic model URL: {_construct_semantic_model_url(data.properties['id'])}",
                deps=upsteam_table_deps,
            )
        )


power_bi_specs = load_powerbi_asset_specs(
    power_bi_workspace,
    dagster_powerbi_translator=CustomDagsterPowerBITranslator,
)

defs = dg.Definitions(assets=[*power_bi_specs], resources={"power_bi": power_bi_workspace})

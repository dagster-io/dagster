import dagster as dg
from dagster_powerbi import (
    DagsterPowerBITranslator,
    PowerBIServicePrincipal,
    PowerBIWorkspace,
    load_powerbi_asset_specs,
)
from dagster_powerbi.translator import PowerBIContentData

# Connect using a service principal
power_bi_workspace = PowerBIWorkspace(
    credentials=PowerBIServicePrincipal(
        client_id=dg.EnvVar("POWER_BI_CLIENT_ID"),
        client_secret=dg.EnvVar("POWER_BI_CLIENT_SECRET"),
        tenant_id=dg.EnvVar("POWER_BI_TENANT_ID"),
    ),
    workspace_id=dg.EnvVar("POWER_BI_WORKSPACE_ID"),
)


class MyCustomPowerBITranslator(DagsterPowerBITranslator):
    def get_report_spec(self, data: PowerBIContentData) -> dg.AssetSpec:
        return (
            super()
            .get_report_spec(data)
            .replace_attributes(
                description=f'Report link: https://app.powerbi.com/groups/{dg.EnvVar("POWER_BI_WORKSPACE_ID").get_value()}/reports/{data.properties["id"]}',
                group_name="BI",
            )
            .merge_attributes(tags={"core_kpis": ""})
        )

    def get_semantic_model_spec(self, data: PowerBIContentData) -> dg.AssetSpec:
        return (
            super()
            .get_semantic_model_spec(data)
            .replace_attributes(
                description=f'Semantic model link: https://app.powerbi.com/groups/{dg.EnvVar("POWER_BI_WORKSPACE_ID").get_value()}/datasets/{data.properties["id"]}/details',
                group_name="BI",
                deps=[
                    dg.AssetKey("calendar"),
                    dg.AssetKey("all_profiles"),
                    dg.AssetKey("latest_feed"),
                    dg.AssetKey("activity_over_time"),
                    dg.AssetKey("top_daily_posts"),
                    dg.AssetKey("to_external_links"),
                ],
                # deps=[dg.AssetKey(path=[dep.asset_key.path[1].upper(), dep.asset_key.path[2]]) for dep in spec.deps],
            )
            .merge_attributes(
                metadata={
                    "dagster/column_schema": dg.TableSchema(
                        columns=[
                            dg.TableColumn(
                                name=col["name"],
                                type=col["dataType"],
                                tags={"PII": ""} if col["name"] == "USER_ID" else None,
                            )
                            for col in data.properties["tables"][0]["columns"]
                        ]
                    )
                },
                tags={"core_kpis": ""},
            )
        )

    # def get_dashboard_spec(self, data: PowerBIContentData) -> dg.AssetSpec:
    #     spec = super().get_dashboard_spec(data)
    #     return replace_attributes(
    #         spec,
    #         group_name="BI"
    #     )

    # def get_data_source_spec(self, data: PowerBIContentData) -> dg.AssetSpec:
    #     spec = super().get_data_source_spec(data)
    #     return replace_attributes(
    #         spec,
    #         group_name="BI"
    #     )


power_bi_specs = load_powerbi_asset_specs(
    power_bi_workspace, dagster_powerbi_translator=MyCustomPowerBITranslator
)
defs = dg.Definitions(assets=[*power_bi_specs], resources={"power_bi": power_bi_workspace})

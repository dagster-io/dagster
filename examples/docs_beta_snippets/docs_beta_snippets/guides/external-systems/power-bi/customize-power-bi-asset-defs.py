import uuid
from typing import cast

from dagster_powerbi import DagsterPowerBITranslator, PowerBIWorkspace
from dagster_powerbi.translator import PowerBIContentData

from dagster import Definitions, EnvVar, asset, define_asset_job
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec

resource = PowerBIWorkspace(
    api_token=EnvVar("POWER_BI_API_TOKEN"),
    workspace_id=EnvVar("POWER_BI_WORKSPACE_ID"),
)


class MyCustomPowerBITranslator(DagsterPowerBITranslator):
    def get_report_spec(self, data: PowerBIContentData) -> AssetSpec:
        return super().get_report_spec(data)._replace(owners=["my_team"])

    def get_semantic_model_spec(self, data: PowerBIContentData) -> AssetSpec:
        return super().get_semantic_model_spec(data)._replace(owners=["my_team"])

    def get_dashboard_spec(self, data: PowerBIContentData) -> AssetSpec:
        return super().get_dashboard_spec(data)._replace(owners=["my_team"])

    def get_dashboard_asset_key(self, data: PowerBIContentData) -> AssetKey:
        return super().get_dashboard_asset_key(data).with_prefix("powerbi")


powerbi_definitions = resource.build_defs()

defs = Definitions.merge(powerbi_definitions)

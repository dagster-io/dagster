import uuid
from typing import cast

from dagster_powerbi import (
    DagsterPowerBITranslator,
    PowerBIServicePrincipal,
    PowerBIWorkspace,
)
from dagster_powerbi.translator import PowerBIContentData

from dagster import Definitions, EnvVar, asset, define_asset_job
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


class MyCustomPowerBITranslator(DagsterPowerBITranslator):
    def get_report_spec(self, data: PowerBIContentData) -> AssetSpec:
        return super().get_report_spec(data)._replace(owners=["my_team"])

    def get_semantic_model_spec(self, data: PowerBIContentData) -> AssetSpec:
        return super().get_semantic_model_spec(data)._replace(owners=["my_team"])

    def get_dashboard_spec(self, data: PowerBIContentData) -> AssetSpec:
        return super().get_dashboard_spec(data)._replace(owners=["my_team"])

    def get_dashboard_asset_key(self, data: PowerBIContentData) -> AssetKey:
        return super().get_dashboard_asset_key(data).with_prefix("powerbi")


defs = resource.build_defs()

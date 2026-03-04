from collections.abc import Mapping
from typing import Any

import dagster as dg
from dagster_dbt import DagsterDbtTranslator, DbtProject
from dagster_dbt.cloud_v2.asset_decorator import dbt_cloud_assets
from dagster_dbt.cloud_v2.resources import DbtCloudWorkspace

from .constants import DBT_UPSTREAMS
from .dbt_cloud_resource import get_dbt_cloud_workspace
from .dbt_cloud_utils import SELECTION_TAG, spec_with_dep


def get_dbt_cloud_assets() -> dg.AssetsDefinition:
    class CustomDagsterDbtTranslator(DagsterDbtTranslator):
        def get_asset_spec(
            self,
            manifest: Mapping[str, Any],
            unique_id: str,
            project: DbtProject | None,
        ) -> dg.AssetSpec:
            default_spec = super().get_asset_spec(
                manifest=manifest, unique_id=unique_id, project=project
            )
            return spec_with_dep(uid_to_dep_mapping=DBT_UPSTREAMS, spec=default_spec)

    @dbt_cloud_assets(
        workspace=get_dbt_cloud_workspace(),
        select=SELECTION_TAG,
        group_name="dbt_cloud",
        dagster_dbt_translator=CustomDagsterDbtTranslator(),
    )
    def _dbt_cloud_assets(context: dg.AssetExecutionContext, dbt_cloud: DbtCloudWorkspace):
        yield from dbt_cloud.cli(args=["build"], context=context).wait()

    _dbt_cloud_assets = _dbt_cloud_assets.map_asset_specs(
        lambda spec: spec.replace_attributes(automation_condition=dg.AutomationCondition.eager())
    )

    return _dbt_cloud_assets

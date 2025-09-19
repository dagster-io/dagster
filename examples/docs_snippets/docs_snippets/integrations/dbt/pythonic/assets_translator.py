from collections.abc import Mapping
from typing import Any

from dagster_dbt import DagsterDbtTranslator, DbtCliResource, dbt_assets

import dagster as dg

from .resources import dbt_project


# start_custom_dagster_dbt_translator
class CustomDagsterDbtTranslator(DagsterDbtTranslator):
    def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> dg.AssetKey:
        asset_key = super().get_asset_key(dbt_resource_props)
        return asset_key.with_prefix("my_prefix_")

    def get_group_name(self, dbt_resource_props: Mapping[str, Any]) -> str:
        # Customize group names
        return "my_dbt_group"


# end_custom_dagster_dbt_translator


@dbt_assets(
    manifest=dbt_project.manifest_path,
    dagster_dbt_translator=CustomDagsterDbtTranslator(),
)
def dbt_models(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()

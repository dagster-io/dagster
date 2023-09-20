from typing import Any, Mapping

from dagster import AssetExecutionContext, AssetKey, file_relative_path
from dagster_dbt import (
    DagsterDbtTranslator,
    DbtCliResource,
    dbt_assets,
    get_asset_key_for_model,
)

DBT_PROJECT_DIR = file_relative_path(__file__, "../../../dbt_project")

dbt_resource = DbtCliResource(project_dir=DBT_PROJECT_DIR)
dbt_parse_invocation = dbt_resource.cli(["parse"]).wait()
dbt_manifest_path = dbt_parse_invocation.target_path.joinpath("manifest.json")


class CustomDagsterDbtTranslator(DagsterDbtTranslator):
    @classmethod
    def get_asset_key(cls, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
        asset_key = super().get_asset_key(dbt_resource_props)

        if dbt_resource_props["resource_type"] == "model":
            asset_key = asset_key.with_prefix(["duckdb", "dbt_schema"])
        if dbt_resource_props["resource_type"] == "source":
            asset_key = asset_key.with_prefix("duckdb")

        return asset_key


@dbt_assets(
    manifest=dbt_manifest_path,
    dagster_dbt_translator=CustomDagsterDbtTranslator(),
)
def dbt_project_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


daily_order_summary_asset_key = get_asset_key_for_model([dbt_project_assets], "daily_order_summary")

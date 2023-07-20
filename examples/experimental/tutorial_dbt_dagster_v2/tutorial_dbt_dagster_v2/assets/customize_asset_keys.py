from typing import Any, Mapping

from dagster import AssetKey, OpExecutionContext
from dagster_dbt import DagsterDbtTranslator, DbtCliResource, dbt_assets

from ..constants import MANIFEST_PATH


class CustomDagsterDbtTranslator(DagsterDbtTranslator):
    @classmethod
    def get_asset_key(cls, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
        return AssetKey(["prefix", dbt_resource_props["alias"]])


@dbt_assets(manifest=MANIFEST_PATH, dagster_dbt_translator=CustomDagsterDbtTranslator())
def my_dbt_assets(context: OpExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()

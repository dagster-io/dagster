from typing import Any, Mapping

from dagster import AssetKey, OpExecutionContext
from dagster_dbt import DagsterDbtTranslator, DbtCli, dbt_assets

from ..constants import MANIFEST_PATH


class CustomDagsterDbtTranslator(DagsterDbtTranslator):
    @classmethod
    def node_info_to_asset_key(cls, node_info: Mapping[str, Any]) -> AssetKey:
        return AssetKey(["prefix", node_info["alias"]])


@dbt_assets(manifest=MANIFEST_PATH, dagster_dbt_translator=CustomDagsterDbtTranslator())
def my_dbt_assets(context: OpExecutionContext, dbt: DbtCli):
    yield from dbt.cli(["build"], context=context).stream()

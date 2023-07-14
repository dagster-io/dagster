from typing import Any, Mapping

from dagster import AssetKey, OpExecutionContext
from dagster_dbt import DagsterDbtTranslator, DbtCli, dbt_assets

from ..constants import MANIFEST_PATH


class CustomDagsterDbtTranslator(DagsterDbtTranslator):
    @classmethod
    def get_asset_key(cls, dbt_repsource_props: Mapping[str, Any]) -> AssetKey:
        return AssetKey(["prefix", dbt_repsource_props["alias"]])


@dbt_assets(manifest=MANIFEST_PATH, dagster_dbt_translator=CustomDagsterDbtTranslator())
def my_dbt_assets(context: OpExecutionContext, dbt: DbtCli):
    yield from dbt.cli(["build"], context=context).stream()

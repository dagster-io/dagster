from typing import Any, Mapping

from dagster import AssetKey, OpExecutionContext
from dagster_dbt.asset_decorator import dbt_assets
from dagster_dbt.cli import DbtCli, DbtManifest

from ..constants import MANIFEST_PATH


class CustomizedDbtManifest(DbtManifest):
    @classmethod
    def node_info_to_asset_key(cls, node_info: Mapping[str, Any]) -> AssetKey:
        return AssetKey(["prefix", node_info["alias"]])


manifest = CustomizedDbtManifest.read(path=MANIFEST_PATH)


@dbt_assets(manifest=manifest)
def my_dbt_assets(context: OpExecutionContext, dbt: DbtCli):
    yield from dbt.cli(["build"], manifest=manifest, context=context).stream()

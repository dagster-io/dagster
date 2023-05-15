from typing import Any, Mapping

from dagster import AssetKey
from dagster_dbt.asset_decorators import dbt_multi_asset
from dagster_dbt.cli.resources_v2 import DbtClientV2, DbtManifest

from tutorial_dbt_dagster_v2.assets import raw_manifest

## Case 6: Customize the individual assets definitions. This replaces:
##   - key_prefix
##   - source_key_prefix
##   - node_info_to_asset_key
##   - node_info_to_group_fn
##   - node_info_to_freshness_policy_fn
##   - node_info_to_auto_materialize_poliicy_fn
##   - node_info_to_definition_metadata_fn
##   - display_raw_sql


class CustomizedDbtManifest(DbtManifest):
    @classmethod
    def node_info_to_asset_key(cls, node_info: Mapping[str, Any]) -> AssetKey:
        return AssetKey(["prefix", node_info["alias"]])


manifest = CustomizedDbtManifest(raw_manifest=raw_manifest)


@dbt_multi_asset(manifest=manifest)
def dbt_assets(dbt: DbtClientV2):
    for event in dbt.cli(["build"]).stream():
        yield from event.to_default_asset_events(manifest=manifest)


dbt_assets = dbt_assets.with_attributes(
    output_asset_key_replacements=manifest.output_asset_key_replacements,
)

from typing import Sequence, Union

import dagster._check as check
from dagster._core.selector.subset_selector import (
    generate_asset_dep_graph,
    generate_asset_name_to_definition_map,
)

from .assets import AssetsDefinition
from .source_asset import SourceAsset


class AssetGraph:
    def __init__(self, all_assets: Sequence[Union[AssetsDefinition, SourceAsset]]):
        assets_defs = []
        source_assets = []
        for asset in all_assets:
            if isinstance(asset, SourceAsset):
                source_assets.append(asset)
            elif isinstance(asset, AssetsDefinition):
                assets_defs.append(asset)
            else:
                check.failed(f"Expected SourceAsset or AssetsDefinition, got {type(asset)}")

        self.assets_defs = assets_defs
        self.asset_dep_graph = generate_asset_dep_graph(assets_defs, source_assets)
        self.all_assets_by_key_str = generate_asset_name_to_definition_map(assets_defs)
        self.source_asset_key_strs = {
            source_asset.key.to_user_string() for source_asset in source_assets
        }

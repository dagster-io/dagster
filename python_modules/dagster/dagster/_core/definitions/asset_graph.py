from typing import Sequence, Union

import dagster._check as check
from dagster._core.selector.subset_selector import generate_asset_dep_graph

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
        self.all_asset_keys = {
            asset_key
            for assets_def in assets_defs
            for asset_key, group in assets_def.group_names_by_key.items()
        }
        self.asset_dep_graph = generate_asset_dep_graph(assets_defs, source_assets)
        self.source_asset_keys = {source_asset.key for source_asset in source_assets}

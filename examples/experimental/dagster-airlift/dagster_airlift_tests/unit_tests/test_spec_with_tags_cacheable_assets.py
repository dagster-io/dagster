from typing import Sequence

from dagster import AssetKey, Definitions, asset
from dagster._core.definitions.asset_key import CoercibleToAssetKey
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)
from dagster_airlift.core.spec_tags_cacheable_assets import SpecWithTagsCacheableAssetsDefinition


class DummyCacheableAssetsDefinition(CacheableAssetsDefinition):
    def __init__(self, asset_key: CoercibleToAssetKey) -> None:
        super().__init__(unique_id="unique_id")
        self.asset_key = AssetKey.from_coercible(asset_key)

    def compute_cacheable_data(self) -> Sequence[AssetsDefinitionCacheableData]:
        return []

    def build_definitions(
        self, data: Sequence[AssetsDefinitionCacheableData]
    ) -> Sequence[AssetsDefinition]:
        @asset(key=self.asset_key)
        def an_asset() -> None: ...

        return [an_asset]


def test_spec_with_tags() -> None:
    c_assets_def = SpecWithTagsCacheableAssetsDefinition(
        wrapped_def=DummyCacheableAssetsDefinition(asset_key="a1"),
        tags={"tag_one": "value_one"},
    )

    assert c_assets_def.unique_id != "unique_id"

    assert isinstance(c_assets_def, CacheableAssetsDefinition)
    assets_def = (
        Definitions(assets=[c_assets_def]).get_asset_graph().assets_def_for_key(AssetKey("a1"))
    )

    assert isinstance(assets_def, AssetsDefinition)
    spec = assets_def.specs_by_key[AssetKey("a1")]
    assert spec.tags == {"tag_one": "value_one"}

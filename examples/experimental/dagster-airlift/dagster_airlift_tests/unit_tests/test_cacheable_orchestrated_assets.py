from typing import Sequence

from dagster import AssetKey, Definitions, asset
from dagster._core.definitions.asset_key import CoercibleToAssetKey
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)
from dagster_airlift.core.dag_defs import dag_defs, task_defs


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


def test_dag_defs_cacheable_assets() -> None:
    defs = dag_defs(
        "dag1",
        task_defs("task1", Definitions(assets=[DummyCacheableAssetsDefinition("asset_1")])),
        task_defs("task2", Definitions(assets=[DummyCacheableAssetsDefinition("asset_2")])),
    )

    assets_def_asset_1 = defs.get_asset_graph().assets_def_for_key(AssetKey("asset_1"))

    assert isinstance(assets_def_asset_1, AssetsDefinition)
    assert assets_def_asset_1.key == AssetKey("asset_1")
    assert assets_def_asset_1.specs_by_key[AssetKey("asset_1")].tags == {
        "airlift/dag_id": "dag1",
        "airlift/task_id": "task1",
    }

    assets_def_asset_2 = defs.get_asset_graph().assets_def_for_key(AssetKey("asset_2"))
    assert assets_def_asset_2.key == AssetKey("asset_2")
    assert assets_def_asset_2.specs_by_key[AssetKey("asset_2")].tags == {
        "airlift/dag_id": "dag1",
        "airlift/task_id": "task2",
    }

import dagster as dg
import pytest
from dagster._check.functions import CheckError
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)
from dagster_components import get_all_passed_assets_as_assets_defs


def test_get_all_passed_assets_as_assets_defs_all_assets_defs():
    @dg.asset
    def my_asset():
        pass

    defs = dg.Definitions(assets=[my_asset])
    assert get_all_passed_assets_as_assets_defs(defs) == [my_asset]


def test_get_all_passed_assets_as_assets_defs_all_asset_specs():
    my_spec = dg.AssetSpec(key="my_asset")
    defs = dg.Definitions(assets=[my_spec])
    assert len(get_all_passed_assets_as_assets_defs(defs)) == 1
    assert get_all_passed_assets_as_assets_defs(defs)[0].key == my_spec.key


def test_get_all_passed_assets_as_assets_defs_cacheable_assets_defs():
    class MyCacheableAssets(CacheableAssetsDefinition):
        def compute_cacheable_data(self):
            return [
                AssetsDefinitionCacheableData(
                    keys_by_input_name={"upstream": AssetKey("upstream")},
                    keys_by_output_name={"result": AssetKey(self.unique_id)},
                )
            ]

        def build_definitions(self, data):
            @dg.op(name=self.unique_id)
            def _op(upstream):
                return upstream + 1

            return [
                dg.AssetsDefinition.from_op(
                    _op,
                    keys_by_input_name=cd.keys_by_input_name,
                    keys_by_output_name=cd.keys_by_output_name,
                )
                for cd in data
            ]

    defs = dg.Definitions(assets=[MyCacheableAssets("a"), MyCacheableAssets("b")])
    with pytest.raises(
        CheckError,
        match="Cannot call get_all_passed_assets_as_assets_defs on a Definitions object that contains CacheableAssetsDefinitions",
    ):
        get_all_passed_assets_as_assets_defs(defs)


def get_all_passed_assets_as_assets_defs_mixed():
    @dg.asset
    def my_asset():
        pass

    my_spec = dg.AssetSpec(key="my_asset")
    defs = dg.Definitions(assets=[my_asset, my_spec])
    assert {asset.key for asset in get_all_passed_assets_as_assets_defs(defs)} == {
        my_asset.key,
        my_spec.key,
    }

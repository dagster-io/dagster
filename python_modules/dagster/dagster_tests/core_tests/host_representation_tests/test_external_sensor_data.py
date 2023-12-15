from typing import AbstractSet

from dagster import AssetKey, AssetSelection, Definitions, asset, sensor
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.host_representation.external_data import external_sensor_data_from_def


def make_three_assets():
    @asset
    def asset1():
        ...

    @asset
    def asset2():
        ...

    @asset
    def asset3():
        ...

    return asset1, asset2, asset3


def test_external_sensor_has_asset_selection():
    @sensor(asset_selection=["asset1", "asset2"])
    def sensor1():
        ...

    defs = Definitions(sensors=[sensor1])

    assert (
        external_sensor_data_from_def(sensor1, defs.get_repository_def()).asset_selection
        == sensor1.asset_selection
    )


def test_unserializable_asset_selection():
    assets = make_three_assets()

    class MySpecialAssetSelection(AssetSelection):
        def resolve_inner(self, asset_graph: AssetGraph) -> AbstractSet[AssetKey]:
            return asset_graph.materializable_asset_keys - {AssetKey("asset3")}

    @sensor(asset_selection=MySpecialAssetSelection())
    def sensor1():
        ...

    defs = Definitions(assets=assets)
    assert external_sensor_data_from_def(
        sensor1, defs.get_repository_def()
    ).asset_selection == AssetSelection.keys("asset1", "asset2")

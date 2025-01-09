from typing import AbstractSet  # noqa: UP035

from dagster import AssetKey, AssetSelection, Definitions, asset, sensor
from dagster._core.definitions.base_asset_graph import BaseAssetGraph
from dagster._core.remote_representation.external_data import SensorSnap


def test_remote_sensor_has_asset_selection():
    @sensor(asset_selection=["asset1", "asset2"])
    def sensor1(): ...

    defs = Definitions(sensors=[sensor1])

    assert (
        SensorSnap.from_def(sensor1, defs.get_repository_def()).asset_selection
        == sensor1.asset_selection
    )


def test_unserializable_asset_selection():
    @asset
    def asset1(): ...

    @asset
    def asset2(): ...

    class MySpecialAssetSelection(AssetSelection):
        def resolve_inner(
            self, asset_graph: BaseAssetGraph, allow_missing: bool
        ) -> AbstractSet[AssetKey]:
            return asset_graph.materializable_asset_keys - {AssetKey("asset2")}

    @sensor(asset_selection=MySpecialAssetSelection())
    def sensor1(): ...

    defs = Definitions(assets=[asset1, asset2])
    assert SensorSnap.from_def(
        sensor1, defs.get_repository_def()
    ).asset_selection == AssetSelection.assets("asset1")

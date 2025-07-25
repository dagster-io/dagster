from typing import AbstractSet  # noqa: UP035

import dagster as dg
from dagster import AssetSelection
from dagster._core.definitions.assets.graph.base_asset_graph import BaseAssetGraph
from dagster._core.remote_representation.external_data import SensorSnap


def test_remote_sensor_has_asset_selection():
    @dg.sensor(asset_selection=["asset1", "asset2"])
    def sensor1(): ...

    defs = dg.Definitions(sensors=[sensor1])

    assert (
        SensorSnap.from_def(sensor1, defs.get_repository_def()).asset_selection
        == sensor1.asset_selection
    )


def test_unserializable_asset_selection():
    @dg.asset
    def asset1(): ...

    @dg.asset
    def asset2(): ...

    class MySpecialAssetSelection(dg.AssetSelection):
        def resolve_inner(
            self, asset_graph: BaseAssetGraph, allow_missing: bool
        ) -> AbstractSet[dg.AssetKey]:
            return asset_graph.materializable_asset_keys - {dg.AssetKey("asset2")}

    @dg.sensor(asset_selection=MySpecialAssetSelection())
    def sensor1(): ...

    defs = dg.Definitions(assets=[asset1, asset2])
    assert SensorSnap.from_def(
        sensor1, defs.get_repository_def()
    ).asset_selection == AssetSelection.assets("asset1")

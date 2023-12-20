from dagster import AssetKey, asset, sensor
from dagster._core.definitions.decorators.repository_decorator import repository
from dagster._core.host_representation.external_data import external_sensor_data_from_def


def test_coerce_to_asset_selection():
    @asset
    def asset1():
        ...

    @asset
    def asset2():
        ...

    @asset
    def asset3():
        ...

    assets = [asset1, asset2, asset3]

    @sensor(asset_selection=["asset1", "asset2"])
    def sensor1():
        ...

    assert sensor1.asset_selection.resolve(assets) == {AssetKey("asset1"), AssetKey("asset2")}

    @sensor(asset_selection=[asset1, asset2])
    def sensor2():
        ...

    assert sensor2.asset_selection.resolve(assets) == {AssetKey("asset1"), AssetKey("asset2")}


def test_external_sensor_has_asset_selection():
    @asset
    def asset1():
        ...

    @asset
    def asset2():
        ...

    @asset
    def asset3():
        ...

    @sensor(asset_selection=["asset1", "asset2"])
    def sensor1():
        ...

    @repository
    def my_repo():
        return [
            sensor1,
        ]

    assert (
        external_sensor_data_from_def(sensor1, my_repo).asset_selection == sensor1.asset_selection
    )

from dagster import AssetKey, asset, sensor


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

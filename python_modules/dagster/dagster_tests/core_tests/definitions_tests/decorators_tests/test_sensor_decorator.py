import dagster as dg
from dagster._core.definitions.metadata.metadata_value import MetadataValue


def test_coerce_to_asset_selection():
    @dg.asset
    def asset1(): ...

    @dg.asset
    def asset2(): ...

    @dg.asset
    def asset3(): ...

    assets = [asset1, asset2, asset3]

    @dg.sensor(asset_selection=["asset1", "asset2"])
    def sensor1(): ...

    assert sensor1.asset_selection.resolve(assets) == {dg.AssetKey("asset1"), dg.AssetKey("asset2")}  # pyright: ignore[reportOptionalMemberAccess]

    @dg.sensor(asset_selection=[asset1, asset2])
    def sensor2(): ...

    assert sensor2.asset_selection.resolve(assets) == {dg.AssetKey("asset1"), dg.AssetKey("asset2")}  # pyright: ignore[reportOptionalMemberAccess]


def test_jobless_sensor_uses_eval_fn_name():
    @dg.asset
    def asset1(): ...

    @dg.sensor(target=asset1)
    def my_sensor():
        pass

    assert my_sensor.name == "my_sensor"


def test_sensor_tags():
    @dg.sensor(tags={"foo": "bar"})
    def my_sensor():
        pass

    # auto-serialized to JSON
    assert my_sensor.tags == {"foo": "bar"}


def test_sensor_metadata():
    @dg.sensor(metadata={"foo": "bar"})
    def my_sensor():
        pass

    # auto-serialized to JSON
    assert my_sensor.metadata["foo"] == MetadataValue.text("bar")

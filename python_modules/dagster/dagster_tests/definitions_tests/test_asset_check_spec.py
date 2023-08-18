from dagster import AssetCheckSpec, AssetKey


def test_coerce_asset_key():
    assert AssetCheckSpec(asset_key="foo", name="check1").asset_key == AssetKey("foo")

from dagster import AssetKey, build_output_context


def test_build_output_context_asset_key():
    assert build_output_context(asset_key="apple").asset_key == AssetKey("apple")
    assert build_output_context(asset_key=["apple", "banana"]).asset_key == AssetKey(
        ["apple", "banana"]
    )
    assert build_output_context(asset_key=AssetKey("apple")).asset_key == AssetKey("apple")

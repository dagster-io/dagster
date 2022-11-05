from dagster import AssetMaterialization


def test_asset_materialization_metadata():
    materialization = AssetMaterialization(asset_key="abc", metadata={"a": "b", "c": 1})
    assert materialization.metadata["a"].value == "b"
    assert materialization.metadata["c"].value == 1

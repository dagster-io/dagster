import dagster as dg


def test_asset_materialization_metadata():
    materialization = dg.AssetMaterialization(asset_key="abc", metadata={"a": "b", "c": 1})
    assert materialization.metadata["a"].value == "b"
    assert materialization.metadata["c"].value == 1


def test_asset_materialization_tags():
    dg.AssetMaterialization("asset1", tags={"dagster/reporting_user": "someone@dagster.io"})


def test_asset_materialization_asset_level_metadata_keys():
    materialization1 = dg.AssetMaterialization("asset1", asset_level_metadata_keys=["a", "b"])
    assert materialization1.asset_level_metadata_keys == ["a", "b"]

    materialization2 = dg.AssetMaterialization("asset2", asset_level_metadata_keys=None)
    assert materialization2.asset_level_metadata_keys is None

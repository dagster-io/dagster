import dagster as dg


def test_asset_materialization_metadata():
    materialization = dg.AssetMaterialization(asset_key="abc", metadata={"a": "b", "c": 1})
    assert materialization.metadata["a"].value == "b"
    assert materialization.metadata["c"].value == 1


def test_asset_materialization_tags():
    dg.AssetMaterialization("asset1", tags={"dagster/reporting_user": "someone@dagster.io"})

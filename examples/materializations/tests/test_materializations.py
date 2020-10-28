from dagster import AssetKey, DagsterInstance, execute_pipeline

from ..repo import materialization_pipeline


def test_materialized_assets():
    instance = DagsterInstance.ephemeral()
    res = execute_pipeline(materialization_pipeline, instance=instance)
    assert res.success
    assert instance.is_asset_aware
    asset_keys = instance.all_asset_keys()
    assert len(asset_keys) == 1
    assert asset_keys[0] == AssetKey(["dashboards", "analytics_dashboard"])

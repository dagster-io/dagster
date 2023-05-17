from dagster import AssetKey, StaticPartitionsDefinition, asset
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.asset_reconciliation_sensor import (
    AssetReconciliationCursor,
)

partitions = StaticPartitionsDefinition(partition_keys=["a", "b", "c"])


@asset(partitions_def=partitions)
def my_asset(_):
    pass


def test_asset_reconciliation_cursor_evaluation_id():
    backcompat_serialized = (
        """[20, ["a"], {"my_asset": "{\\"version\\": 1, \\"subset\\": [\\"a\\"]}"}]"""
    )

    asset_graph = AssetGraph.from_assets([my_asset])
    c = AssetReconciliationCursor.from_serialized(backcompat_serialized, asset_graph)

    assert c == AssetReconciliationCursor(
        20,
        {AssetKey("a")},
        {AssetKey("my_asset"): partitions.empty_subset().with_partition_keys(["a"])},
        None,
    )

    c2 = c.with_updates(
        21, [], {AssetKey("my_asset")}, {AssetKey("my_asset"): {"a"}}, 1, asset_graph
    )

    serdes_c2 = AssetReconciliationCursor.from_serialized(c2.serialize(), asset_graph)
    assert serdes_c2 == c2
    assert serdes_c2.evaluation_id == 1

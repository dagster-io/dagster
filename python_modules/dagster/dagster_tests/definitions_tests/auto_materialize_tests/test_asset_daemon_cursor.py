import datetime
import json

from dagster import AssetKey, StaticPartitionsDefinition, asset
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonAssetCursor, AssetDaemonCursor
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.asset_subset import AssetSubset

partitions = StaticPartitionsDefinition(partition_keys=["a", "b", "c"])


@asset(partitions_def=partitions)
def my_asset(_):
    pass


def test_asset_reconciliation_cursor_evaluation_id_backcompat() -> None:
    backcompat_serialized = (
        """[20, ["a"], {"my_asset": "{\\"version\\": 1, \\"subset\\": [\\"a\\"]}"}]"""
    )

    assert AssetDaemonCursor.get_evaluation_id_from_serialized(backcompat_serialized) is None

    asset_graph = AssetGraph.from_assets([my_asset])
    c = AssetDaemonCursor.from_serialized(backcompat_serialized, asset_graph)

    assert c == AssetDaemonCursor(
        20,
        {AssetKey("a")},
        {AssetKey("my_asset"): partitions.empty_subset().with_partition_keys(["a"])},
        0,
        {},
        {},
        0,
    )

    c2 = c.with_updates(
        21,
        1,
        [],
        0,
        [],
        datetime.datetime.now(),
        [],
    )

    serdes_c2 = AssetDaemonCursor.from_serialized(c2.serialize(), asset_graph)
    assert serdes_c2 == c2
    assert serdes_c2.evaluation_id == 1

    assert AssetDaemonCursor.get_evaluation_id_from_serialized(c2.serialize()) == 1


def test_asset_cursor_partitioned_to_unpartitioned():
    partitions_def = StaticPartitionsDefinition(["a", "b", "c"])

    @asset(name="asset1", partitions_def=partitions_def)
    def asset1_partitioned():
        pass

    @asset(name="asset1")
    def asset1_unpartitioned():
        pass

    asset_key = AssetKey(["asset1"])

    unpartitioned_subset = AssetSubset(asset_key=AssetKey(["asset1"]), value=True)

    partitioned_subset = AssetSubset.empty(asset_key, partitions_def)

    cursor = AssetDaemonAssetCursor(
        asset_key=AssetKey(["asset1"]),
        latest_storage_id=1,
        latest_evaluation_timestamp=None,
        latest_evaluation=None,
        materialized_requested_or_discarded_subset=unpartitioned_subset,
    )

    # unpartitioned to partitioned

    c2 = cursor.with_updates(
        AssetGraph.from_assets([asset1_partitioned]),
        newly_materialized_subset=partitioned_subset,
        requested_asset_partitions=set(),
        discarded_asset_partitions=set(),
    )

    assert c2.materialized_requested_or_discarded_subset == partitioned_subset

    # partitioned back to unpartitioned

    c3 = c2.with_updates(
        AssetGraph.from_assets([asset1_unpartitioned]),
        newly_materialized_subset=unpartitioned_subset,
        requested_asset_partitions=set(),
        discarded_asset_partitions=set(),
    )

    assert c3.materialized_requested_or_discarded_subset == unpartitioned_subset


def test_asset_reconciliation_cursor_auto_observe_backcompat():
    partitions_def = StaticPartitionsDefinition(["a", "b", "c"])

    @asset(partitions_def=partitions_def)
    def asset1():
        ...

    @asset
    def asset2():
        ...

    handled_root_partitions_by_asset_key = {
        asset1.key: partitions_def.subset_with_partition_keys(["a", "b"])
    }
    handled_root_asset_keys = {asset2.key}
    serialized = json.dumps(
        (
            25,
            [key.to_user_string() for key in handled_root_asset_keys],
            {
                key.to_user_string(): subset.serialize()
                for key, subset in handled_root_partitions_by_asset_key.items()
            },
        )
    )

    cursor = AssetDaemonCursor.from_serialized(
        serialized, asset_graph=AssetGraph.from_assets([asset1, asset2])
    )
    assert cursor.latest_storage_id == 25
    assert cursor.handled_root_asset_keys == handled_root_asset_keys
    assert cursor.handled_root_partitions_by_asset_key == handled_root_partitions_by_asset_key

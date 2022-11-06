# pylint: disable=unused-argument

from dagster import (
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
    StaticPartitionsDefinition,
    asset,
)
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.events import AssetKeyPartitionKey


def test_basics():
    @asset
    def asset0():
        ...

    @asset(partitions_def=DailyPartitionsDefinition(start_date="2022-01-01"))
    def asset1(asset0):
        ...

    @asset(partitions_def=DailyPartitionsDefinition(start_date="2022-01-01"))
    def asset2(asset0):
        ...

    @asset(partitions_def=HourlyPartitionsDefinition(start_date="2022-01-01-00:00"))
    def asset3(asset1, asset2):
        ...

    asset_graph = AssetGraph([asset0, asset1, asset2, asset3])
    assert asset_graph.all_asset_keys == {asset0.key, asset1.key, asset2.key, asset3.key}
    assert not asset_graph.is_partitioned(asset0.key)
    assert asset_graph.is_partitioned(asset1.key)
    assert asset_graph.have_same_partitioning(asset1.key, asset2.key)
    assert not asset_graph.have_same_partitioning(asset1.key, asset3.key)
    assert asset_graph.get_children(asset0.key) == {asset1.key, asset2.key}
    assert asset_graph.get_parents(asset3.key) == {asset1.key, asset2.key}


def test_get_children_partitions_unpartitioned_parent_partitioned_child():
    @asset
    def parent():
        ...

    @asset(partitions_def=StaticPartitionsDefinition(["a", "b"]))
    def child(parent):
        ...

    asset_graph = AssetGraph([parent, child])
    assert asset_graph.get_children_partitions(parent.key) == set(
        [AssetKeyPartitionKey(child.key, "a"), AssetKeyPartitionKey(child.key, "b")]
    )


def test_get_parent_partitions_unpartitioned_child_partitioned_parent():
    @asset(partitions_def=StaticPartitionsDefinition(["a", "b"]))
    def parent():
        ...

    @asset
    def child(parent):
        ...

    asset_graph = AssetGraph([parent, child])
    assert asset_graph.get_parents_partitions(child.key) == set(
        [AssetKeyPartitionKey(parent.key, "a"), AssetKeyPartitionKey(parent.key, "b")]
    )


def test_get_children_partitions_fan_out():
    @asset(partitions_def=DailyPartitionsDefinition(start_date="2022-01-01"))
    def parent():
        ...

    @asset(partitions_def=HourlyPartitionsDefinition(start_date="2022-01-01-00:00"))
    def child(parent):
        ...

    asset_graph = AssetGraph([parent, child])
    assert asset_graph.get_children_partitions(parent.key, "2022-01-03") == set(
        [
            AssetKeyPartitionKey(child.key, f"2022-01-03-{str(hour).zfill(2)}:00")
            for hour in range(24)
        ]
    )


def test_get_parent_partitions_fan_in():
    @asset(partitions_def=HourlyPartitionsDefinition(start_date="2022-01-01-00:00"))
    def parent():
        ...

    @asset(partitions_def=DailyPartitionsDefinition(start_date="2022-01-01"))
    def child(parent):
        ...

    asset_graph = AssetGraph([parent, child])
    assert asset_graph.get_parents_partitions(child.key, "2022-01-03") == set(
        [
            AssetKeyPartitionKey(parent.key, f"2022-01-03-{str(hour).zfill(2)}:00")
            for hour in range(24)
        ]
    )

# pylint: disable=unused-argument
import pendulum
import pytest

from dagster import (
    AssetIn,
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
    LastPartitionMapping,
    PartitionMapping,
    StaticPartitionsDefinition,
    asset,
    repository,
)
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.host_representation.external_data import external_asset_graph_from_defs
from dagster._seven.compat.pendulum import create_pendulum_time


def to_external_asset_graph(assets) -> AssetGraph:
    @repository
    def repo():
        return assets

    external_asset_nodes = external_asset_graph_from_defs(
        repo.get_all_pipelines(), source_assets_by_key={}
    )
    return AssetGraph.from_external_assets(external_asset_nodes)


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

    assets = [asset0, asset1, asset2, asset3]
    internal_asset_graph = AssetGraph.from_assets(assets)
    external_asset_graph = to_external_asset_graph(assets)

    def assert_stuff(asset_graph):
        assert asset_graph.all_asset_keys == {asset0.key, asset1.key, asset2.key, asset3.key}
        assert not asset_graph.is_partitioned(asset0.key)
        assert asset_graph.is_partitioned(asset1.key)
        assert asset_graph.have_same_partitioning(asset1.key, asset2.key)
        assert not asset_graph.have_same_partitioning(asset1.key, asset3.key)
        assert asset_graph.get_children(asset0.key) == {asset1.key, asset2.key}
        assert asset_graph.get_parents(asset3.key) == {asset1.key, asset2.key}

    assert_stuff(internal_asset_graph)
    assert_stuff(external_asset_graph)


def test_get_children_partitions_unpartitioned_parent_partitioned_child():
    @asset
    def parent():
        ...

    @asset(partitions_def=StaticPartitionsDefinition(["a", "b"]))
    def child(parent):
        ...

    internal_asset_graph = AssetGraph.from_assets([parent, child])
    external_asset_graph = to_external_asset_graph([parent, child])
    assert internal_asset_graph.get_children_partitions(parent.key) == set(
        [AssetKeyPartitionKey(child.key, "a"), AssetKeyPartitionKey(child.key, "b")]
    )
    assert external_asset_graph.get_children_partitions(parent.key) == set(
        [AssetKeyPartitionKey(child.key, "a"), AssetKeyPartitionKey(child.key, "b")]
    )


def test_get_parent_partitions_unpartitioned_child_partitioned_parent():
    @asset(partitions_def=StaticPartitionsDefinition(["a", "b"]))
    def parent():
        ...

    @asset
    def child(parent):
        ...

    internal_asset_graph = AssetGraph.from_assets([parent, child])
    external_asset_graph = to_external_asset_graph([parent, child])
    assert internal_asset_graph.get_parents_partitions(child.key) == set(
        [AssetKeyPartitionKey(parent.key, "a"), AssetKeyPartitionKey(parent.key, "b")]
    )
    assert external_asset_graph.get_parents_partitions(child.key) == set(
        [AssetKeyPartitionKey(parent.key, "a"), AssetKeyPartitionKey(parent.key, "b")]
    )


def test_get_children_partitions_fan_out():
    @asset(partitions_def=DailyPartitionsDefinition(start_date="2022-01-01"))
    def parent():
        ...

    @asset(partitions_def=HourlyPartitionsDefinition(start_date="2022-01-01-00:00"))
    def child(parent):
        ...

    internal_asset_graph = AssetGraph.from_assets([parent, child])
    external_asset_graph = to_external_asset_graph([parent, child])
    assert internal_asset_graph.get_children_partitions(parent.key, "2022-01-03") == set(
        [
            AssetKeyPartitionKey(child.key, f"2022-01-03-{str(hour).zfill(2)}:00")
            for hour in range(24)
        ]
    )

    assert external_asset_graph.get_children_partitions(parent.key, "2022-01-03") == set(
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

    internal_asset_graph = AssetGraph.from_assets([parent, child])
    external_asset_graph = to_external_asset_graph([parent, child])
    assert internal_asset_graph.get_parents_partitions(child.key, "2022-01-03") == set(
        [
            AssetKeyPartitionKey(parent.key, f"2022-01-03-{str(hour).zfill(2)}:00")
            for hour in range(24)
        ]
    )
    assert external_asset_graph.get_parents_partitions(child.key, "2022-01-03") == set(
        [
            AssetKeyPartitionKey(parent.key, f"2022-01-03-{str(hour).zfill(2)}:00")
            for hour in range(24)
        ]
    )


def test_get_parent_partitions_non_default_partition_mapping():
    @asset(partitions_def=DailyPartitionsDefinition(start_date="2022-01-01"))
    def parent():
        ...

    @asset(ins={"parent": AssetIn(partition_mapping=LastPartitionMapping())})
    def child(parent):
        ...

    internal_asset_graph = AssetGraph.from_assets([parent, child])
    external_asset_graph = to_external_asset_graph([parent, child])

    with pendulum.test(create_pendulum_time(year=2022, month=1, day=3, hour=4)):
        assert internal_asset_graph.get_parents_partitions(child.key) == {
            AssetKeyPartitionKey(parent.key, "2022-01-02")
        }
        assert external_asset_graph.get_parents_partitions(child.key) == {
            AssetKeyPartitionKey(parent.key, "2022-01-02")
        }


def test_custom_unsupported_partition_mapping():
    class TrailingWindowPartitionMapping(PartitionMapping):
        def get_upstream_partitions_for_partition_range(
            self, downstream_partition_key_range, downstream_partitions_def, upstream_partitions_def
        ) -> PartitionKeyRange:
            assert downstream_partitions_def
            assert upstream_partitions_def

            start, end = downstream_partition_key_range
            return PartitionKeyRange(str(max(1, int(start) - 1)), end)

        def get_downstream_partitions_for_partition_range(
            self, upstream_partition_key_range, downstream_partitions_def, upstream_partitions_def
        ) -> PartitionKeyRange:
            raise NotImplementedError()

    @asset(partitions_def=StaticPartitionsDefinition(["1", "2", "3"]))
    def parent():
        ...

    with pytest.warns(
        DeprecationWarning,
        match="Non-built-in PartitionMappings, such as TrailingWindowPartitionMapping are "
        "deprecated and will not work with asset reconciliation. The built-in partition mappings "
        "are AllPartitionMapping, IdentityPartitionMapping",
    ):

        @asset(
            partitions_def=StaticPartitionsDefinition(["1", "2", "3"]),
            ins={"parent": AssetIn(partition_mapping=TrailingWindowPartitionMapping())},
        )
        def child(parent):
            ...

    internal_asset_graph = AssetGraph.from_assets([parent, child])
    external_asset_graph = to_external_asset_graph([parent, child])
    assert internal_asset_graph.get_parents_partitions(child.key, "2") == {
        AssetKeyPartitionKey(parent.key, "1"),
        AssetKeyPartitionKey(parent.key, "2"),
    }
    # external falls back to default PartitionMapping
    assert external_asset_graph.get_parents_partitions(child.key, "2") == {
        AssetKeyPartitionKey(parent.key, "2")
    }

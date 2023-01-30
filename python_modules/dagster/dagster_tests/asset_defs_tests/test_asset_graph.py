# pylint: disable=unused-argument
from unittest.mock import MagicMock

import pendulum
import pytest
from dagster import (
    AssetIn,
    AssetKey,
    AssetOut,
    AssetsDefinition,
    DailyPartitionsDefinition,
    GraphOut,
    HourlyPartitionsDefinition,
    LastPartitionMapping,
    Out,
    PartitionMapping,
    StaticPartitionsDefinition,
    asset,
    graph,
    multi_asset,
    op,
    repository,
)
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.external_asset_graph import ExternalAssetGraph
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.host_representation.external_data import external_asset_graph_from_defs
from dagster._seven.compat.pendulum import create_pendulum_time
from dagster._core.test_utils import instance_for_test


def to_external_asset_graph(assets) -> AssetGraph:
    @repository
    def repo():
        return assets

    external_asset_nodes = external_asset_graph_from_defs(
        repo.get_all_pipelines(), source_assets_by_key={}
    )
    return ExternalAssetGraph.from_repository_handles_and_external_asset_nodes(
        [(MagicMock(), asset_node) for asset_node in external_asset_nodes]
    )


def test_basics():
    @asset(code_version="1")
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
        for asset_def in assets:
            assert asset_graph.get_required_multi_asset_keys(asset_def.key) == set()
        assert asset_graph.get_code_version(asset0.key) == "1"
        assert asset_graph.get_code_version(asset1.key) is None

    assert_stuff(internal_asset_graph)
    assert_stuff(external_asset_graph)


def test_get_children_partitions_unpartitioned_parent_partitioned_child():
    @asset
    def parent():
        ...

    @asset(partitions_def=StaticPartitionsDefinition(["a", "b"]))
    def child(parent):
        ...

    with instance_for_test() as instance:
        internal_asset_graph = AssetGraph.from_assets([parent, child])
        external_asset_graph = to_external_asset_graph([parent, child])
        assert internal_asset_graph.get_children_partitions(instance, parent.key) == set(
            [AssetKeyPartitionKey(child.key, "a"), AssetKeyPartitionKey(child.key, "b")]
        )
        assert external_asset_graph.get_children_partitions(instance, parent.key) == set(
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
        match=(
            "Non-built-in PartitionMappings, such as TrailingWindowPartitionMapping are deprecated"
            " and will not work with asset reconciliation. The built-in partition mappings are"
            " AllPartitionMapping, IdentityPartitionMapping"
        ),
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


def test_required_multi_asset_sets_non_subsettable_multi_asset():
    @multi_asset(outs={"a": AssetOut(dagster_type=None), "b": AssetOut(dagster_type=None)})
    def non_subsettable_multi_asset():
        ...

    for asset_graph in [
        AssetGraph.from_assets([non_subsettable_multi_asset]),
        to_external_asset_graph([non_subsettable_multi_asset]),
    ]:
        for asset_key in non_subsettable_multi_asset.keys:
            assert (
                asset_graph.get_required_multi_asset_keys(asset_key)
                == non_subsettable_multi_asset.keys
            )


def test_required_multi_asset_sets_subsettable_multi_asset():
    @multi_asset(
        outs={"a": AssetOut(dagster_type=None), "b": AssetOut(dagster_type=None)}, can_subset=True
    )
    def subsettable_multi_asset():
        ...

    for asset_graph in [
        AssetGraph.from_assets([subsettable_multi_asset]),
        to_external_asset_graph([subsettable_multi_asset]),
    ]:
        for asset_key in subsettable_multi_asset.keys:
            assert asset_graph.get_required_multi_asset_keys(asset_key) == set()


def test_required_multi_asset_sets_graph_backed_multi_asset():
    @op
    def op1():
        return 1

    @op(out={"b": Out(), "c": Out()})
    def op2():
        return 4, 5

    @graph(out={"a": GraphOut(), "b": GraphOut(), "c": GraphOut()})
    def graph1():
        a = op1()
        b, c = op2()
        return a, b, c

    graph_backed_multi_asset = AssetsDefinition.from_graph(graph1)
    for asset_graph in [
        AssetGraph.from_assets([graph_backed_multi_asset]),
        to_external_asset_graph([graph_backed_multi_asset]),
    ]:
        for asset_key in graph_backed_multi_asset.keys:
            assert (
                asset_graph.get_required_multi_asset_keys(asset_key)
                == graph_backed_multi_asset.keys
            )


def test_required_multi_asset_sets_same_op_in_different_assets():
    @op
    def op1():
        ...

    asset1 = AssetsDefinition.from_op(op1, keys_by_output_name={"result": AssetKey("a")})
    asset2 = AssetsDefinition.from_op(op1, keys_by_output_name={"result": AssetKey("b")})
    assets = [asset1, asset2]

    for asset_graph in [AssetGraph.from_assets(assets), to_external_asset_graph(assets)]:
        for asset_def in assets:
            assert asset_graph.get_required_multi_asset_keys(asset_def.key) == set()


def test_get_non_source_roots_missing_source():
    @asset
    def foo():
        pass

    @asset(non_argument_deps={"this_source_is_fake", "source_asset"})
    def bar(foo):
        pass

    source_asset = SourceAsset("source_asset")

    asset_graph = AssetGraph.from_assets([foo, bar, source_asset])
    assert asset_graph.get_non_source_roots(AssetKey("bar")) == {AssetKey("foo")}


def test_partitioned_source_asset():
    partitions_def = DailyPartitionsDefinition(start_date="2022-01-01")

    partitioned_source = SourceAsset(
        "partitioned_source",
        partitions_def=partitions_def,
    )

    @asset(partitions_def=partitions_def, non_argument_deps={"partitioned_source"})
    def downstream_of_partitioned_source():
        pass

    asset_graph = AssetGraph.from_assets([partitioned_source, downstream_of_partitioned_source])

    assert asset_graph.is_partitioned(AssetKey("partitioned_source"))
    assert asset_graph.is_partitioned(AssetKey("downstream_of_partitioned_source"))

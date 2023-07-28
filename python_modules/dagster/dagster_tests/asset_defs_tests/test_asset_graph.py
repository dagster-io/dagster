from datetime import datetime
from typing import Optional
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
    TimeWindowPartitionMapping,
    asset,
    graph,
    multi_asset,
    op,
    repository,
)
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.external_asset_graph import ExternalAssetGraph
from dagster._core.definitions.partition import PartitionsDefinition, PartitionsSubset
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.partition_mapping import UpstreamPartitionsResult
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.host_representation.external_data import external_asset_graph_from_defs
from dagster._core.instance import DynamicPartitionsStore
from dagster._core.test_utils import instance_for_test
from dagster._seven.compat.pendulum import create_pendulum_time


def to_external_asset_graph(assets) -> AssetGraph:
    @repository
    def repo():
        return assets

    external_asset_nodes = external_asset_graph_from_defs(
        repo.get_all_jobs(), source_assets_by_key={}
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
        current_time = pendulum.now("UTC")

        internal_asset_graph = AssetGraph.from_assets([parent, child])
        external_asset_graph = to_external_asset_graph([parent, child])
        assert internal_asset_graph.get_children_partitions(
            instance, current_time, parent.key
        ) == set([AssetKeyPartitionKey(child.key, "a"), AssetKeyPartitionKey(child.key, "b")])
        assert external_asset_graph.get_children_partitions(
            instance, current_time, parent.key
        ) == set([AssetKeyPartitionKey(child.key, "a"), AssetKeyPartitionKey(child.key, "b")])


def test_get_parent_partitions_unpartitioned_child_partitioned_parent():
    @asset(partitions_def=StaticPartitionsDefinition(["a", "b"]))
    def parent():
        ...

    @asset
    def child(parent):
        ...

    internal_asset_graph = AssetGraph.from_assets([parent, child])
    external_asset_graph = to_external_asset_graph([parent, child])

    with instance_for_test() as instance:
        current_time = pendulum.now("UTC")

        assert internal_asset_graph.get_parents_partitions(
            instance, current_time, child.key
        ).parent_partitions == set(
            [AssetKeyPartitionKey(parent.key, "a"), AssetKeyPartitionKey(parent.key, "b")]
        )

        assert external_asset_graph.get_parents_partitions(
            instance, current_time, child.key
        ).parent_partitions == set(
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
    with instance_for_test() as instance:
        current_time = pendulum.now("UTC")

        assert internal_asset_graph.get_children_partitions(
            instance, current_time, parent.key, "2022-01-03"
        ) == set(
            [
                AssetKeyPartitionKey(child.key, f"2022-01-03-{str(hour).zfill(2)}:00")
                for hour in range(24)
            ]
        )

        assert external_asset_graph.get_children_partitions(
            instance, current_time, parent.key, "2022-01-03"
        ) == set(
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
    with instance_for_test() as instance:
        current_time = pendulum.now("UTC")

        assert internal_asset_graph.get_parents_partitions(
            instance, current_time, child.key, "2022-01-03"
        ).parent_partitions == set(
            [
                AssetKeyPartitionKey(parent.key, f"2022-01-03-{str(hour).zfill(2)}:00")
                for hour in range(24)
            ]
        )

        assert external_asset_graph.get_parents_partitions(
            instance, current_time, child.key, "2022-01-03"
        ).parent_partitions == set(
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
        with instance_for_test() as instance:
            current_time = pendulum.now("UTC")

            mapped_partitions_result = internal_asset_graph.get_parents_partitions(
                instance, current_time, child.key
            )
            mapped_partitions_result.parent_partitions == {
                AssetKeyPartitionKey(parent.key, "2022-01-02")
            }
            mapped_partitions_result.required_but_nonexistent_parents_partitions == {}

            mapped_partitions_result = external_asset_graph.get_parents_partitions(
                instance, current_time, child.key
            )
            mapped_partitions_result.parent_partitions == {
                AssetKeyPartitionKey(parent.key, "2022-01-02")
            }
            mapped_partitions_result.required_but_nonexistent_parents_partitions == {}


def test_custom_unsupported_partition_mapping():
    class TrailingWindowPartitionMapping(PartitionMapping):
        def get_upstream_mapped_partitions_result_for_partitions(
            self,
            downstream_partitions_subset: Optional[PartitionsSubset],
            upstream_partitions_def: PartitionsDefinition,
            current_time: Optional[datetime] = None,
            dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
        ) -> UpstreamPartitionsResult:
            assert downstream_partitions_subset
            assert upstream_partitions_def

            partition_keys = list(downstream_partitions_subset.get_partition_keys())
            return UpstreamPartitionsResult(
                upstream_partitions_def.empty_subset().with_partition_key_range(
                    PartitionKeyRange(str(max(1, int(partition_keys[0]) - 1)), partition_keys[-1])
                ),
                [],
            )

        def get_downstream_partitions_for_partitions(
            self,
            upstream_partitions_subset: PartitionsSubset,
            downstream_partitions_def: PartitionsDefinition,
            current_time: Optional[datetime] = None,
            dynamic_partitions_store: Optional[DynamicPartitionsStore] = None,
        ) -> PartitionsSubset:
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

    with instance_for_test() as instance:
        current_time = pendulum.now("UTC")

        assert internal_asset_graph.get_parents_partitions(
            instance, current_time, child.key, "2"
        ).parent_partitions == {
            AssetKeyPartitionKey(parent.key, "1"),
            AssetKeyPartitionKey(parent.key, "2"),
        }

        # external falls back to default PartitionMapping
        assert external_asset_graph.get_parents_partitions(
            instance, current_time, child.key, "2"
        ).parent_partitions == {AssetKeyPartitionKey(parent.key, "2")}


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

    @asset(deps=["this_source_is_fake", "source_asset"])
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

    @asset(partitions_def=partitions_def, deps=["partitioned_source"])
    def downstream_of_partitioned_source():
        pass

    asset_graph = AssetGraph.from_assets([partitioned_source, downstream_of_partitioned_source])

    assert asset_graph.is_partitioned(AssetKey("partitioned_source"))
    assert asset_graph.is_partitioned(AssetKey("downstream_of_partitioned_source"))


def test_bfs_filter_asset_subsets():
    daily_partitions_def = DailyPartitionsDefinition(start_date="2022-01-01")

    @asset(partitions_def=daily_partitions_def)
    def asset0():
        ...

    @asset(partitions_def=daily_partitions_def)
    def asset1(asset0):
        ...

    @asset(partitions_def=daily_partitions_def)
    def asset2(asset0):
        ...

    @asset(partitions_def=HourlyPartitionsDefinition(start_date="2022-01-01-00:00"))
    def asset3(asset1, asset2):
        ...

    asset_graph = AssetGraph.from_assets([asset0, asset1, asset2, asset3])

    def include_all(asset_key, partitions_subset):
        return True

    initial_partitions_subset = daily_partitions_def.empty_subset().with_partition_keys(
        ["2022-01-02", "2022-01-03"]
    )
    initial_asset1_subset = AssetGraphSubset(
        asset_graph, partitions_subsets_by_asset_key={asset1.key: initial_partitions_subset}
    )
    corresponding_asset3_subset = AssetGraphSubset(
        asset_graph,
        partitions_subsets_by_asset_key={
            asset3.key: asset3.partitions_def.empty_subset().with_partition_key_range(
                PartitionKeyRange("2022-01-02-00:00", "2022-01-03-23:00")
            ),
        },
    )

    assert (
        asset_graph.bfs_filter_subsets(
            dynamic_partitions_store=MagicMock(),
            initial_subset=initial_asset1_subset,
            condition_fn=include_all,
            current_time=pendulum.now("UTC"),
        )
        == initial_asset1_subset | corresponding_asset3_subset
    )

    def include_none(asset_key, partitions_subset):
        return False

    assert asset_graph.bfs_filter_subsets(
        dynamic_partitions_store=MagicMock(),
        initial_subset=initial_asset1_subset,
        condition_fn=include_none,
        current_time=pendulum.now("UTC"),
    ) == AssetGraphSubset(asset_graph)

    def exclude_asset3(asset_key, partitions_subset):
        return asset_key is not asset3.key

    assert (
        asset_graph.bfs_filter_subsets(
            dynamic_partitions_store=MagicMock(),
            initial_subset=initial_asset1_subset,
            condition_fn=exclude_asset3,
            current_time=pendulum.now("UTC"),
        )
        == initial_asset1_subset
    )

    def exclude_asset2(asset_key, partitions_subset):
        return asset_key is not asset2.key

    initial_asset0_subset = AssetGraphSubset(
        asset_graph, partitions_subsets_by_asset_key={asset0.key: initial_partitions_subset}
    )
    assert (
        asset_graph.bfs_filter_subsets(
            dynamic_partitions_store=MagicMock(),
            initial_subset=initial_asset0_subset,
            condition_fn=exclude_asset2,
            current_time=pendulum.now("UTC"),
        )
        == initial_asset0_subset | initial_asset1_subset | corresponding_asset3_subset
    )


def test_bfs_filter_asset_subsets_different_mappings():
    daily_partitions_def = DailyPartitionsDefinition(start_date="2022-01-01")

    @asset(partitions_def=daily_partitions_def)
    def asset0():
        ...

    @asset(partitions_def=daily_partitions_def)
    def asset1(asset0):
        ...

    @asset(
        partitions_def=daily_partitions_def,
        ins={
            "asset0": AssetIn(
                partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=-1)
            )
        },
    )
    def asset2(asset0):
        ...

    @asset(partitions_def=daily_partitions_def)
    def asset3(asset1, asset2):
        ...

    asset_graph = AssetGraph.from_assets([asset0, asset1, asset2, asset3])

    def include_all(asset_key, partitions_subset):
        return True

    initial_subset = daily_partitions_def.subset_with_partition_keys(["2022-01-01"])
    expected_asset2_partitions_subset = daily_partitions_def.subset_with_partition_keys(
        ["2022-01-02"]
    )
    expected_asset3_partitions_subset = daily_partitions_def.subset_with_partition_keys(
        ["2022-01-01", "2022-01-02"]
    )
    expected_asset_graph_subset = AssetGraphSubset(
        asset_graph,
        partitions_subsets_by_asset_key={
            asset0.key: initial_subset,
            asset1.key: initial_subset,
            asset2.key: expected_asset2_partitions_subset,
            asset3.key: expected_asset3_partitions_subset,
        },
    )

    assert (
        asset_graph.bfs_filter_subsets(
            dynamic_partitions_store=MagicMock(),
            initial_subset=AssetGraphSubset(
                asset_graph,
                partitions_subsets_by_asset_key={asset0.key: initial_subset},
            ),
            condition_fn=include_all,
            current_time=pendulum.now("UTC"),
        )
        == expected_asset_graph_subset
    )

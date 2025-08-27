from typing import cast

import dagster as dg
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView
from dagster._core.asset_graph_view.bfs import (
    AssetGraphViewBfsFilterConditionResult,
    bfs_filter_asset_graph_view,
)
from dagster._core.definitions.assets.graph.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._time import create_datetime


def _get_subset_with_keys(graph_view, keys):
    return AssetGraphSubset.from_entity_subsets(
        [graph_view.get_full_subset(key=key) for key in keys]
    )


def test_bfs_filter_empty_graph():
    """Test BFS filter on empty graph returns empty result."""
    graph_view = AssetGraphView.for_test(dg.Definitions())
    initial_subset = AssetGraphSubset.create_empty_subset()

    def condition_fn(subset, _visited):
        return AssetGraphViewBfsFilterConditionResult(subset, [])

    result, failed = bfs_filter_asset_graph_view(
        graph_view, condition_fn, initial_subset, include_full_execution_set=False
    )

    assert result == AssetGraphSubset.create_empty_subset()
    assert failed == []


def test_bfs_filter_dependency_chain():
    """Test BFS filter on linear dependency chain."""

    @dg.asset
    def asset1():
        return 1

    @dg.asset
    def asset2(asset1):
        return asset1 + 1

    @dg.asset
    def asset3(asset2):
        return asset2 + 1

    @dg.asset
    def asset4(asset3):
        return asset3 + 1

    graph_view = AssetGraphView.for_test(dg.Definitions(assets=[asset1, asset2, asset3, asset4]))
    initial_subset = AssetGraphSubset.from_entity_subsets(
        [graph_view.get_full_subset(key=asset1.key)]
    )

    def condition_fn(subset, visited):
        # Only allow asset1 and asset2
        if dg.AssetKey("asset3") in subset.asset_keys:
            assert visited == AssetGraphSubset.from_entity_subsets(
                [
                    graph_view.get_full_subset(key=asset1.key),
                    graph_view.get_full_subset(key=asset2.key),
                ]
            )

            return AssetGraphViewBfsFilterConditionResult(
                AssetGraphSubset.create_empty_subset(),
                [(subset, "asset3 not allowed")],
            )
        return AssetGraphViewBfsFilterConditionResult(subset, [])

    result, failed = bfs_filter_asset_graph_view(
        graph_view, condition_fn, initial_subset, include_full_execution_set=False
    )

    assert result == AssetGraphSubset.from_entity_subsets(
        [graph_view.get_full_subset(key=asset1.key), graph_view.get_full_subset(key=asset2.key)]
    )
    assert len(failed) == 1
    assert failed[0][0] == AssetGraphSubset.from_entity_subsets(
        [graph_view.get_full_subset(key=asset3.key)]
    )
    assert failed[0][1] == "asset3 not allowed"


def test_bfs_filter_multi_asset():
    """Test BFS filter with multi-asset."""

    @dg.asset
    def a():
        return 1

    @dg.asset
    def b():
        return 2

    @dg.multi_asset(
        specs=[dg.AssetSpec("c", deps=["a"]), dg.AssetSpec("d", deps=["b"])]
    )  # d is level 1, e is level 3, gets assigned 3
    def my_multi_asset():
        pass

    @dg.asset
    def e(d):
        pass

    graph_view = AssetGraphView.for_test(dg.Definitions(assets=[a, b, my_multi_asset, e]))
    initial_subset = _get_subset_with_keys(graph_view, [a.key])

    def condition_fn(subset, _visited):
        return AssetGraphViewBfsFilterConditionResult(subset, [])

    result_without_full_execution_set, _failed = bfs_filter_asset_graph_view(
        graph_view, condition_fn, initial_subset, include_full_execution_set=False
    )

    assert result_without_full_execution_set == _get_subset_with_keys(
        graph_view, [a.key, dg.AssetKey(["c"])]
    )

    result_with_full_execution_set, _failed = bfs_filter_asset_graph_view(
        graph_view, condition_fn, initial_subset, include_full_execution_set=True
    )

    assert result_with_full_execution_set == _get_subset_with_keys(
        graph_view, [a.key, dg.AssetKey(["c"]), dg.AssetKey(["d"]), e.key]
    )


def test_bfs_filter_diamond():
    """Test BFS filter with a diamond-shaped graph to ensure bottom node is visited once."""

    @dg.asset
    def top():
        return 1

    @dg.asset
    def left(top):
        return top + 1

    @dg.asset
    def right(top):
        return top + 2

    @dg.asset
    def bottom(left, right):
        return left + right

    graph_view = AssetGraphView.for_test(dg.Definitions(assets=[top, left, right, bottom]))
    initial_subset = _get_subset_with_keys(graph_view, [dg.AssetKey("top")])

    visit_count = {}

    def condition_fn(subset, _visited):
        for key in subset.asset_keys:
            visit_count[key] = visit_count.get(key, 0) + 1
        return AssetGraphViewBfsFilterConditionResult(subset, [])

    result, failed = bfs_filter_asset_graph_view(
        graph_view, condition_fn, initial_subset, include_full_execution_set=True
    )

    # Each node should be visited exactly once
    assert visit_count == {
        dg.AssetKey("bottom"): 1,
        dg.AssetKey("left"): 1,
        dg.AssetKey("right"): 1,
        dg.AssetKey("top"): 1,
    }
    assert result == _get_subset_with_keys(
        graph_view,
        [dg.AssetKey("top"), dg.AssetKey("left"), dg.AssetKey("right"), dg.AssetKey("bottom")],
    )
    assert failed == []


def test_bfs_filter_with_partitions():
    """Test BFS filter with partitioned assets where condition filters some partitions."""

    @dg.asset(partitions_def=dg.StaticPartitionsDefinition(["a", "b", "c"]))
    def upstream():
        return 1

    @dg.asset(
        partitions_def=dg.StaticPartitionsDefinition(["a", "b", "c"]),
        ins={"upstream": dg.AssetIn(partition_mapping=dg.IdentityPartitionMapping())},
    )
    def downstream(upstream):
        return upstream + 1

    graph_view = AssetGraphView.for_test(dg.Definitions(assets=[upstream, downstream]))
    initial_subset = AssetGraphSubset.from_asset_partition_set(
        {
            AssetKeyPartitionKey(dg.AssetKey(["upstream"]), "a"),
            AssetKeyPartitionKey(dg.AssetKey(["upstream"]), "b"),
        },
        graph_view.asset_graph,
    )

    def condition_fn(subset, _visited):
        # Only allow partition "a" for upstream and corresponding mapped partition "x" for downstream
        included = set()
        excluded = set()

        for entity_subset in graph_view.iterate_asset_subsets(subset):
            for asset_partition in entity_subset.expensively_compute_asset_partitions():
                if asset_partition.partition_key == "b":
                    excluded.add(asset_partition)
                else:
                    included.add(asset_partition)

        return AssetGraphViewBfsFilterConditionResult(
            AssetGraphSubset.from_asset_partition_set(included, graph_view.asset_graph),
            (
                [
                    (
                        AssetGraphSubset.from_asset_partition_set(excluded, graph_view.asset_graph),
                        "b is not welcome here",
                    )
                ]
                if excluded
                else []
            ),
        )

    result, failed = bfs_filter_asset_graph_view(
        graph_view, condition_fn, initial_subset, include_full_execution_set=True
    )

    # Should only include partition "a" for upstream and "x" for downstream
    assert result == AssetGraphSubset.from_asset_partition_set(
        {
            AssetKeyPartitionKey(dg.AssetKey(["upstream"]), "a"),
            AssetKeyPartitionKey(dg.AssetKey(["downstream"]), "a"),
        },
        graph_view.asset_graph,
    )

    assert failed == [
        (
            AssetGraphSubset.from_asset_partition_set(
                {
                    AssetKeyPartitionKey(dg.AssetKey(["upstream"]), "b"),
                },
                graph_view.asset_graph,
            ),
            "b is not welcome here",
        ),
    ]


def test_bfs_filter_time_window_partitions():
    # Create assets with daily partitions
    daily_partitions = dg.DailyPartitionsDefinition(start_date="2023-01-01")
    hourly_partitions = dg.HourlyPartitionsDefinition(start_date="2023-01-01-00:00")

    @dg.asset(partitions_def=daily_partitions)
    def upstream():
        pass

    @dg.asset(partitions_def=hourly_partitions)
    def downstream(upstream) -> None:
        pass

    graph_view = AssetGraphView.for_test(dg.Definitions(assets=[upstream, downstream]))

    # Initial subset with multiple days
    initial_subset = AssetGraphSubset.from_asset_partition_set(
        {
            AssetKeyPartitionKey(dg.AssetKey(["upstream"]), "2023-01-01"),
            AssetKeyPartitionKey(dg.AssetKey(["upstream"]), "2023-01-02"),
            AssetKeyPartitionKey(dg.AssetKey(["upstream"]), "2023-01-03"),
        },
        graph_view.asset_graph,
    )

    def condition_fn(subset, visited):
        # Filter out weekends
        included = set()
        excluded = set()

        for entity_subset in graph_view.iterate_asset_subsets(subset):
            for asset_partition in entity_subset.expensively_compute_asset_partitions():
                partition_date = (
                    cast(
                        "dg.TimeWindowPartitionsDefinition",
                        graph_view.asset_graph.get(entity_subset.key).partitions_def,
                    )
                    .time_window_for_partition_key(asset_partition.partition_key)
                    .start
                )
                if partition_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                    excluded.add(asset_partition)
                else:
                    included.add(asset_partition)

        return AssetGraphViewBfsFilterConditionResult(
            AssetGraphSubset.from_asset_partition_set(included, graph_view.asset_graph),
            (
                [
                    (
                        AssetGraphSubset.from_asset_partition_set(excluded, graph_view.asset_graph),
                        "Weekend partitions are excluded",
                    )
                ]
                if excluded
                else []
            ),
        )

    result, failed = bfs_filter_asset_graph_view(
        graph_view, condition_fn, initial_subset, include_full_execution_set=True
    )

    # Jan 1, 2023 was a Sunday
    assert result == AssetGraphSubset(
        partitions_subsets_by_asset_key={
            dg.AssetKey(["upstream"]): daily_partitions.get_partition_subset_in_time_window(
                dg.TimeWindow(start=create_datetime(2023, 1, 2), end=create_datetime(2023, 1, 4))
            ),
            dg.AssetKey(["downstream"]): hourly_partitions.get_partition_subset_in_time_window(
                dg.TimeWindow(start=create_datetime(2023, 1, 2), end=create_datetime(2023, 1, 4))
            ),
        }
    )

    assert failed == [
        (
            AssetGraphSubset.from_asset_partition_set(
                {
                    AssetKeyPartitionKey(dg.AssetKey(["upstream"]), "2023-01-01"),
                },
                graph_view.asset_graph,
            ),
            "Weekend partitions are excluded",
        ),
    ]


def test_bfs_filter_self_dependent_asset():
    daily_partitions_def = dg.DailyPartitionsDefinition(start_date="2023-01-01")

    @dg.asset(
        partitions_def=daily_partitions_def,
        deps=[
            dg.AssetDep(
                "self_dependent",
                partition_mapping=dg.TimeWindowPartitionMapping(start_offset=-1, end_offset=-1),
            ),
        ],
    )
    def self_dependent(context) -> None:
        pass

    graph_view = AssetGraphView.for_test(dg.Definitions([self_dependent]))

    initial_subset = AssetGraphSubset.from_asset_partition_set(
        {
            AssetKeyPartitionKey(dg.AssetKey(["self_dependent"]), "2023-01-01"),
            AssetKeyPartitionKey(dg.AssetKey(["self_dependent"]), "2023-01-02"),
        },
        graph_view.asset_graph,
    )

    def condition_fn(subset, _visited):
        included = set()
        excluded = set()

        for asset_partition in subset.iterate_asset_partitions():
            partition_key = asset_partition.partition_key
            if partition_key == "2023-01-05":
                excluded.add(asset_partition)
            else:
                included.add(asset_partition)

        return AssetGraphViewBfsFilterConditionResult(
            AssetGraphSubset.from_asset_partition_set(included, graph_view.asset_graph),
            (
                [
                    (
                        AssetGraphSubset.from_asset_partition_set(excluded, graph_view.asset_graph),
                        "2023-01-05 excluded",
                    )
                ]
                if excluded
                else []
            ),
        )

    result, failed = bfs_filter_asset_graph_view(
        graph_view, condition_fn, initial_subset, include_full_execution_set=True
    )

    assert result == AssetGraphSubset(
        partitions_subsets_by_asset_key={
            dg.AssetKey("self_dependent"): daily_partitions_def.get_partition_subset_in_time_window(
                dg.TimeWindow(start=create_datetime(2023, 1, 1), end=create_datetime(2023, 1, 5))
            ),
        }
    )

    assert failed == [
        (
            AssetGraphSubset.from_asset_partition_set(
                {
                    AssetKeyPartitionKey(dg.AssetKey("self_dependent"), "2023-01-05"),
                },
                graph_view.asset_graph,
            ),
            "2023-01-05 excluded",
        ),
    ]

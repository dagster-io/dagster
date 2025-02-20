from typing import cast

from dagster import (
    AssetDep,
    AssetKey,
    AssetSpec,
    DailyPartitionsDefinition,
    Definitions,
    HourlyPartitionsDefinition,
    TimeWindow,
    TimeWindowPartitionMapping,
    TimeWindowPartitionsDefinition,
    asset,
    multi_asset,
)
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView
from dagster._core.asset_graph_view.bfs import (
    AssetGraphViewBfsFilterConditionResult,
    bfs_filter_asset_graph_view,
)
from dagster._core.definitions.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.partition_mapping import IdentityPartitionMapping
from dagster._time import create_datetime


def _get_subset_with_keys(graph_view, keys):
    return AssetGraphSubset.from_entity_subsets(
        [graph_view.get_full_subset(key=key) for key in keys]
    )


def test_bfs_filter_empty_graph():
    """Test BFS filter on empty graph returns empty result."""
    graph_view = AssetGraphView.for_test(Definitions())
    initial_subset = AssetGraphSubset.empty()

    def condition_fn(subset, _visited):
        return AssetGraphViewBfsFilterConditionResult(subset, [])

    result, failed = bfs_filter_asset_graph_view(
        graph_view, condition_fn, initial_subset, include_full_execution_set=False
    )

    assert result == AssetGraphSubset.empty()
    assert failed == []


def test_bfs_filter_dependency_chain():
    """Test BFS filter on linear dependency chain."""

    @asset
    def asset1():
        return 1

    @asset
    def asset2(asset1):
        return asset1 + 1

    @asset
    def asset3(asset2):
        return asset2 + 1

    @asset
    def asset4(asset3):
        return asset3 + 1

    graph_view = AssetGraphView.for_test(Definitions(assets=[asset1, asset2, asset3, asset4]))
    initial_subset = AssetGraphSubset.from_entity_subsets(
        [graph_view.get_full_subset(key=asset1.key)]
    )

    def condition_fn(subset, visited):
        # Only allow asset1 and asset2
        if AssetKey("asset3") in subset.asset_keys:
            assert visited == AssetGraphSubset.from_entity_subsets(
                [
                    graph_view.get_full_subset(key=asset1.key),
                    graph_view.get_full_subset(key=asset2.key),
                ]
            )

            return AssetGraphViewBfsFilterConditionResult(
                AssetGraphSubset.empty(),
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

    @asset
    def a():
        return 1

    @asset
    def b():
        return 2

    @multi_asset(
        specs=[AssetSpec("c", deps=["a"]), AssetSpec("d", deps=["b"])]
    )  # d is level 1, e is level 3, gets assigned 3
    def my_multi_asset():
        pass

    @asset
    def e(d):
        pass

    graph_view = AssetGraphView.for_test(Definitions(assets=[a, b, my_multi_asset, e]))
    initial_subset = _get_subset_with_keys(graph_view, [a.key])

    def condition_fn(subset, _visited):
        return AssetGraphViewBfsFilterConditionResult(subset, [])

    result_without_full_execution_set, _failed = bfs_filter_asset_graph_view(
        graph_view, condition_fn, initial_subset, include_full_execution_set=False
    )

    assert result_without_full_execution_set == _get_subset_with_keys(
        graph_view, [a.key, AssetKey(["c"])]
    )

    result_with_full_execution_set, _failed = bfs_filter_asset_graph_view(
        graph_view, condition_fn, initial_subset, include_full_execution_set=True
    )

    assert result_with_full_execution_set == _get_subset_with_keys(
        graph_view, [a.key, AssetKey(["c"]), AssetKey(["d"]), e.key]
    )


def test_bfs_filter_diamond():
    """Test BFS filter with a diamond-shaped graph to ensure bottom node is visited once."""

    @asset
    def top():
        return 1

    @asset
    def left(top):
        return top + 1

    @asset
    def right(top):
        return top + 2

    @asset
    def bottom(left, right):
        return left + right

    graph_view = AssetGraphView.for_test(Definitions(assets=[top, left, right, bottom]))
    initial_subset = _get_subset_with_keys(graph_view, [AssetKey("top")])

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
        AssetKey("bottom"): 1,
        AssetKey("left"): 1,
        AssetKey("right"): 1,
        AssetKey("top"): 1,
    }
    assert result == _get_subset_with_keys(
        graph_view, [AssetKey("top"), AssetKey("left"), AssetKey("right"), AssetKey("bottom")]
    )
    assert failed == []


from dagster import AssetIn, StaticPartitionsDefinition


def test_bfs_filter_with_partitions():
    """Test BFS filter with partitioned assets where condition filters some partitions."""

    @asset(partitions_def=StaticPartitionsDefinition(["a", "b", "c"]))
    def upstream():
        return 1

    @asset(
        partitions_def=StaticPartitionsDefinition(["a", "b", "c"]),
        ins={"upstream": AssetIn(partition_mapping=IdentityPartitionMapping())},
    )
    def downstream(upstream):
        return upstream + 1

    graph_view = AssetGraphView.for_test(Definitions(assets=[upstream, downstream]))
    initial_subset = AssetGraphSubset.from_asset_partition_set(
        {
            AssetKeyPartitionKey(AssetKey(["upstream"]), "a"),
            AssetKeyPartitionKey(AssetKey(["upstream"]), "b"),
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
            AssetKeyPartitionKey(AssetKey(["upstream"]), "a"),
            AssetKeyPartitionKey(AssetKey(["downstream"]), "a"),
        },
        graph_view.asset_graph,
    )

    assert failed == [
        (
            AssetGraphSubset.from_asset_partition_set(
                {
                    AssetKeyPartitionKey(AssetKey(["upstream"]), "b"),
                },
                graph_view.asset_graph,
            ),
            "b is not welcome here",
        ),
    ]


def test_bfs_filter_time_window_partitions():
    # Create assets with daily partitions
    daily_partitions = DailyPartitionsDefinition(start_date="2023-01-01")
    hourly_partitions = HourlyPartitionsDefinition(start_date="2023-01-01-00:00")

    @asset(partitions_def=daily_partitions)
    def upstream():
        pass

    @asset(partitions_def=hourly_partitions)
    def downstream(upstream) -> None:
        pass

    graph_view = AssetGraphView.for_test(Definitions(assets=[upstream, downstream]))

    # Initial subset with multiple days
    initial_subset = AssetGraphSubset.from_asset_partition_set(
        {
            AssetKeyPartitionKey(AssetKey(["upstream"]), "2023-01-01"),
            AssetKeyPartitionKey(AssetKey(["upstream"]), "2023-01-02"),
            AssetKeyPartitionKey(AssetKey(["upstream"]), "2023-01-03"),
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
                        TimeWindowPartitionsDefinition,
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
            AssetKey(["upstream"]): daily_partitions.get_partition_subset_in_time_window(
                TimeWindow(start=create_datetime(2023, 1, 2), end=create_datetime(2023, 1, 4))
            ),
            AssetKey(["downstream"]): hourly_partitions.get_partition_subset_in_time_window(
                TimeWindow(start=create_datetime(2023, 1, 2), end=create_datetime(2023, 1, 4))
            ),
        }
    )

    assert failed == [
        (
            AssetGraphSubset.from_asset_partition_set(
                {
                    AssetKeyPartitionKey(AssetKey(["upstream"]), "2023-01-01"),
                },
                graph_view.asset_graph,
            ),
            "Weekend partitions are excluded",
        ),
    ]


def test_bfs_filter_self_dependent_asset():
    daily_partitions_def = DailyPartitionsDefinition(start_date="2023-01-01")

    @asset(
        partitions_def=daily_partitions_def,
        deps=[
            AssetDep(
                "self_dependent",
                partition_mapping=TimeWindowPartitionMapping(start_offset=-1, end_offset=-1),
            ),
        ],
    )
    def self_dependent(context) -> None:
        pass

    graph_view = AssetGraphView.for_test(Definitions([self_dependent]))

    initial_subset = AssetGraphSubset.from_asset_partition_set(
        {
            AssetKeyPartitionKey(AssetKey(["self_dependent"]), "2023-01-01"),
            AssetKeyPartitionKey(AssetKey(["self_dependent"]), "2023-01-02"),
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
            AssetKey("self_dependent"): daily_partitions_def.get_partition_subset_in_time_window(
                TimeWindow(start=create_datetime(2023, 1, 1), end=create_datetime(2023, 1, 5))
            ),
        }
    )

    assert failed == [
        (
            AssetGraphSubset.from_asset_partition_set(
                {
                    AssetKeyPartitionKey(AssetKey("self_dependent"), "2023-01-05"),
                },
                graph_view.asset_graph,
            ),
            "2023-01-05 excluded",
        ),
    ]

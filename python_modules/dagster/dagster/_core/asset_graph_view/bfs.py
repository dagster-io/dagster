from collections.abc import Iterable, Sequence
from functools import total_ordering
from heapq import heapify, heappop, heappush
from typing import TYPE_CHECKING, Callable, NamedTuple

import dagster._check as check
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView
from dagster._core.asset_graph_view.serializable_entity_subset import SerializableEntitySubset
from dagster._core.definitions.assets.graph.asset_graph_subset import AssetGraphSubset

if TYPE_CHECKING:
    from dagster._core.asset_graph_view.entity_subset import EntitySubset


class AssetGraphViewBfsFilterConditionResult(NamedTuple):
    passed_asset_graph_subset: AssetGraphSubset
    excluded_asset_graph_subsets_and_reasons: Sequence[tuple[AssetGraphSubset, str]]


def bfs_filter_asset_graph_view(
    asset_graph_view: AssetGraphView,
    condition_fn: Callable[
        ["AssetGraphSubset", "AssetGraphSubset"],
        AssetGraphViewBfsFilterConditionResult,
    ],
    initial_asset_graph_subset: "AssetGraphSubset",
    include_full_execution_set: bool,
    traverse_self_dependent_assets: bool = True,
) -> tuple[AssetGraphSubset, Sequence[tuple[AssetGraphSubset, str]]]:
    """Returns the subset of the graph that satisfy supplied criteria.

    - Are >= initial_asset_graph_subset
    - Match the condition_fn
    - Any of their ancestors >= initial_asset_graph_subset match the condition_fn

    Also returns a list of tuples, where each tuple is an asset subset that did not
    satisfy the condition and the reason they were filtered out.

    The condition_fn takes in:
    - a subset of the asset graph to evaluate the condition for. If include_full_execution_set=True,
    the asset keys are all part of the same execution set (i.e. non-subsettable multi-asset). If
    include_full_execution_set=False, only a single asset key will be in the subset.

    - An AssetGraphSubset for the portion of the graph that has so far been visited and passed
    the condition.

    The condition_fn should return a object with an AssetGraphSubset indicating the portion
    of the subset that passes the condition, and a list of (AssetGraphSubset, str)
    tuples with more information about why certain subsets were excluded.

    Visits parents before children.
    """
    initial_subsets = list(asset_graph_view.iterate_asset_subsets(initial_asset_graph_subset))

    # invariant: we never consider an asset partition before considering its ancestors
    queue = ToposortedPriorityQueue(
        asset_graph_view, initial_subsets, include_full_execution_set=include_full_execution_set
    )

    visited_graph_subset = initial_asset_graph_subset

    result: AssetGraphSubset = AssetGraphSubset.create_empty_subset()
    failed_reasons: Sequence[tuple[AssetGraphSubset, str]] = []

    asset_graph = asset_graph_view.asset_graph

    while len(queue) > 0:
        candidate_subset = queue.dequeue()
        condition_result = condition_fn(candidate_subset, result)

        subset_that_meets_condition = condition_result.passed_asset_graph_subset
        failed_reasons.extend(condition_result.excluded_asset_graph_subsets_and_reasons)

        result = result | subset_that_meets_condition

        for matching_entity_subset in asset_graph_view.iterate_asset_subsets(
            subset_that_meets_condition
        ):
            # Add any child subsets that have not yet been visited to the queue
            for child_key in asset_graph.get(matching_entity_subset.key).child_keys:
                if not traverse_self_dependent_assets and child_key == matching_entity_subset.key:
                    continue

                child_subset = asset_graph_view.compute_child_subset(
                    child_key, matching_entity_subset
                )
                unvisited_child_subset = child_subset.compute_difference(
                    asset_graph_view.get_entity_subset_from_asset_graph_subset(
                        visited_graph_subset, child_key
                    )
                )
                if not unvisited_child_subset.is_empty:
                    queue.enqueue(unvisited_child_subset)
                    visited_graph_subset = (
                        visited_graph_subset
                        | AssetGraphSubset.from_entity_subsets([unvisited_child_subset])
                    )

    return result, failed_reasons


class ToposortedPriorityQueue:
    """Queue that returns parents before their children."""

    @total_ordering
    class QueueItem(NamedTuple):
        level: int
        sort_key: str
        asset_graph_subset: AssetGraphSubset

        def __eq__(self, other: object) -> bool:
            if isinstance(other, ToposortedPriorityQueue.QueueItem):
                return self.level == other.level and self.sort_key == other.sort_key
            return False

        def __lt__(self, other: object) -> bool:
            if isinstance(other, ToposortedPriorityQueue.QueueItem):
                return self.level < other.level or (
                    self.level == other.level and self.sort_key < other.sort_key
                )
            raise TypeError()

    def __init__(
        self,
        asset_graph_view: AssetGraphView,
        items: Iterable["EntitySubset"],
        include_full_execution_set: bool,
    ):
        self._asset_graph_view = asset_graph_view
        self._include_full_execution_set = include_full_execution_set

        self._toposort_level_by_asset_key = {
            asset_key: i
            for i, asset_keys in enumerate(
                asset_graph_view.asset_graph.toposorted_asset_keys_by_level
            )
            for asset_key in asset_keys
        }
        self._heap = [self._queue_item(entity_subset) for entity_subset in items]
        heapify(self._heap)

    def enqueue(self, entity_subset: "EntitySubset") -> None:
        heappush(self._heap, self._queue_item(entity_subset))

    def dequeue(self) -> AssetGraphSubset:
        # For multi-assets, will include all required multi-asset keys if
        # include_full_execution_set is set to True, or just the passed in
        # asset key if it was not. If there are multiple assets in the subset
        # the subset will have the same partitions included for each asset.
        #
        # Returns the union of all subsets that share the same sort key
        # (i.e. asset key).

        # the minimum item in a heap is always at index 0
        min_item = self._heap[0]

        result = AssetGraphSubset.create_empty_subset()
        # Collect all items with the same minimum sort key (asset key)
        while self._heap and self._heap[0].sort_key == min_item.sort_key:
            heap_value = heappop(self._heap)
            result |= heap_value.asset_graph_subset

        return result

    def _queue_item(self, entity_subset: "EntitySubset") -> "ToposortedPriorityQueue.QueueItem":
        asset_key = entity_subset.key

        if self._include_full_execution_set:
            execution_set_keys = self._asset_graph_view.asset_graph.get(
                asset_key
            ).execution_set_asset_keys
        else:
            execution_set_keys = {asset_key}

        level = max(
            self._toposort_level_by_asset_key[asset_key] for asset_key in execution_set_keys
        )

        serializable_entity_subset = entity_subset.convert_to_serializable_subset()

        serializable_entity_subsets = [
            SerializableEntitySubset(key=asset_key, value=serializable_entity_subset.value)
            for asset_key in execution_set_keys
        ]

        entity_subsets = [
            check.not_none(
                self._asset_graph_view.get_subset_from_serializable_subset(
                    serializable_entity_subset
                )
            )
            for serializable_entity_subset in serializable_entity_subsets
        ]

        asset_graph_subset = AssetGraphSubset.from_entity_subsets(entity_subsets)

        return ToposortedPriorityQueue.QueueItem(
            level,
            asset_key.to_string(),
            asset_graph_subset=asset_graph_subset,
        )

    def __len__(self) -> int:
        return len(self._heap)

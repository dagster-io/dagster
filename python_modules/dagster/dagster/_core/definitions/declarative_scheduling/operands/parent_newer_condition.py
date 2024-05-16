from typing import AbstractSet

from dagster._core.asset_graph_view.asset_graph_view import AssetSlice
from dagster._core.definitions.declarative_scheduling.scheduling_condition import (
    SchedulingCondition,
    SchedulingResult,
)
from dagster._core.definitions.declarative_scheduling.scheduling_context import SchedulingContext
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._serdes.serdes import whitelist_for_serdes


@whitelist_for_serdes
class ParentNewerCondition(SchedulingCondition):
    @property
    def description(self) -> str:
        return "At least one parent has been updated more recently than the candidate."

    def compute_newer_parents(
        self, context: SchedulingContext, candidate: AssetKeyPartitionKey
    ) -> AbstractSet[AssetKeyPartitionKey]:
        """Returns the set of parent asset partitions that are newer than the candidate."""
        # TODO: replace this implementation with one backed by the StaleStatusResolver
        candidate_slice = context.asset_graph_view.get_asset_slice_from_asset_partitions(
            {candidate}
        )
        parent_slices = candidate_slice.compute_parent_slices()
        all_parent_asset_partitions = {
            ap
            for parent_slice in parent_slices.values()
            for ap in parent_slice.expensively_compute_asset_partitions()
        }
        return (
            context.legacy_context.instance_queryer.get_parent_asset_partitions_updated_after_child(
                asset_partition=candidate,
                parent_asset_partitions=all_parent_asset_partitions,
                respect_materialization_data_versions=False,
                ignored_parent_keys=set(),
            )
        )

    def compute_parent_newer_slice(
        self, context: SchedulingContext, from_slice: AssetSlice
    ) -> AssetSlice:
        """For a given slice, computes the slice for which at least one parent is newer than the
        given asset partition.
        """
        asset_partitions_with_updated_parents = {
            ap
            for ap in from_slice.expensively_compute_asset_partitions()
            if len(self.compute_newer_parents(context, ap)) > 0
        }
        return (
            context.asset_graph_view.get_asset_slice_from_asset_partitions(
                asset_partitions_with_updated_parents
            )
            if asset_partitions_with_updated_parents
            else context.asset_graph_view.create_empty_slice(context.asset_key)
        )

    def compute_slice_to_evaluate(self, context: SchedulingContext) -> AssetSlice:
        """Computes the slice of the target asset that must be fully evaluated this tick."""
        if context.previous_evaluation_max_storage_id is None:
            # on the first tick, evaluate all candidates, as you have no previous information
            return context.candidate_slice
        else:
            # on subsequent ticks, only evaluate candidates if they were not evaluated on the
            # previous tick, or have been updated since the previous tick, or have parents that
            # have been updated since the previous tick
            if context.previous_candidate_slice:
                new_candidates = context.candidate_slice.compute_difference(
                    context.previous_candidate_slice
                )
            else:
                new_candidates = context.candidate_slice

            # candidates that have updated since the previous tick
            newly_updated_slice = context.asset_graph_view.compute_updated_since_cursor_slice(
                asset_key=context.asset_key, cursor=context.previous_evaluation_max_storage_id
            )
            # candidates that have parents that have updated since the previous tick
            parent_newly_updated_slice = (
                context.asset_graph_view.compute_parent_updated_since_cursor_slice(
                    asset_key=context.asset_key,
                    cursor=context.previous_evaluation_max_storage_id,
                )
            )
            updated_slice = newly_updated_slice.compute_union(parent_newly_updated_slice)

            return new_candidates.compute_union(
                context.candidate_slice.compute_intersection(updated_slice)
            )

    def evaluate(self, context: SchedulingContext):
        slice_to_evaluate = self.compute_slice_to_evaluate(context)
        new_parent_newer_slice = self.compute_parent_newer_slice(context, slice_to_evaluate)

        if context.previous_evaluation_node and context.previous_evaluation_node.true_slice:
            # combine new results calculated this tick with results from the previous tick
            true_slice = context.previous_evaluation_node.true_slice.compute_difference(
                slice_to_evaluate
            ).compute_union(new_parent_newer_slice)
        else:
            true_slice = new_parent_newer_slice

        return SchedulingResult.create(context, true_slice=true_slice)

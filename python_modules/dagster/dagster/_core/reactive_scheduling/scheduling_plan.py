from typing import NamedTuple, Sequence, Tuple

from dagster._core.execution.backfill import PartitionBackfill
from dagster._core.reactive_scheduling.scheduling_policy import (
    EvaluationResult,
    SchedulingExecutionContext,
    SchedulingPolicy,
)
from dagster._core.utils import make_new_backfill_id

from .asset_graph_view import AssetSlice, PartitionSpace


class ReactiveSchedulingPlan(NamedTuple):
    candidate_partition_space: PartitionSpace
    launch_partition_space: PartitionSpace
    partition_backfill: PartitionBackfill


def build_reactive_scheduling_plan(
    context: SchedulingExecutionContext, starting_slices: Sequence[AssetSlice]
) -> ReactiveSchedulingPlan:
    # todos/questions:
    # * should the starting subset always be unconditionally included? or should it respect evaluation?
    backfill_id = make_new_backfill_id()

    starting_slices = [asset_slice for asset_slice in starting_slices]

    upstream_of_starting_space = create_partition_space_upstream_of_slices(context, starting_slices)

    # candidates start at the root
    initial_candidate_partition_space = upstream_of_starting_space.for_keys(
        upstream_of_starting_space.root_asset_keys
    )

    launch_partition_space, total_candidate_space = build_launch_partition_space(
        context, initial_candidate_partition_space
    )

    tags = {}

    partition_backfill = PartitionBackfill.from_asset_graph_subset(
        backfill_id=backfill_id,
        asset_graph_subset=launch_partition_space.asset_graph_subset,
        backfill_timestamp=context.effective_dt.timestamp(),
        tags=tags,
        dynamic_partitions_store=context.queryer,
    )

    return ReactiveSchedulingPlan(
        partition_backfill=partition_backfill,
        launch_partition_space=launch_partition_space,
        candidate_partition_space=total_candidate_space,
    )


def build_launch_partition_space(
    context: SchedulingExecutionContext, initial_candidate_partition_space: PartitionSpace
) -> Tuple[PartitionSpace, PartitionSpace]:
    launch_partition_space = PartitionSpace.empty(context.asset_graph_view)

    # we build this up as we traverse down the graph
    total_candidate_space = initial_candidate_partition_space

    # now that we have the partition space we descend downward to filter
    for asset_key in context.asset_graph.toposorted_asset_keys:
        candidate_slice = total_candidate_space.get_asset_slice(asset_key)
        asset_info = context.get_scheduling_info(asset_key)
        evaluation_result = (
            asset_info.scheduling_policy.evaluate(context, candidate_slice)
            if asset_info.scheduling_policy
            else EvaluationResult(asset_slice=context.empty_slice(asset_key))
        )

        launch_partition_space = launch_partition_space.with_asset_slice(
            evaluation_result.asset_slice
        )

        # explore one level downward in the candidate partition space
        total_candidate_space = total_candidate_space.with_asset_slices(
            candidate_slice.child_slices
        )

    return launch_partition_space, total_candidate_space


def create_partition_space_upstream_of_slices(
    context: SchedulingExecutionContext, starting_slices: Sequence[AssetSlice]
) -> PartitionSpace:
    upstream_of_starting_space = PartitionSpace.empty(context.asset_graph_view)

    for starting_slice in starting_slices:
        upstream_of_starting_space = upstream_of_starting_space.with_partition_space(
            context.asset_graph_view.create_upstream_partition_space(starting_slice)
        )

    return upstream_of_starting_space

    # rules={
    #     AutoMaterializeRule.materialize_on_missing(),
    #     AutoMaterializeRule.materialize_on_parent_updated(),
    #     AutoMaterializeRule.materialize_on_required_for_freshness(),
    #     AutoMaterializeRule.skip_on_parent_outdated(),
    #     AutoMaterializeRule.skip_on_parent_missing(),
    #     AutoMaterializeRule.skip_on_required_but_nonexistent_parents(),
    #     AutoMaterializeRule.skip_on_backfill_in_progress(),
    # },


class OnAnyNewParentUpdated(SchedulingPolicy):
    def evaluate(
        self, context: SchedulingExecutionContext, current_slice: AssetSlice
    ) -> EvaluationResult:
        return EvaluationResult(asset_slice=RulesLogic.any_parent_updated(context, current_slice))


class Unsynced(SchedulingPolicy):
    def evaluate(
        self, context: SchedulingExecutionContext, current_slice: AssetSlice
    ) -> EvaluationResult:
        return EvaluationResult(asset_slice=RulesLogic.unsynced(context, current_slice))


class TargetedByBackfill(SchedulingPolicy):
    def evaluate(
        self, context: SchedulingExecutionContext, current_slice: AssetSlice
    ) -> EvaluationResult:
        raise NotImplementedError()
        # return EvaluationResult(asset_slice=current_slice.backfill_targeted_slice.inverse)


class RulesLogic:
    @staticmethod
    def latest_complete_time_window(
        context: SchedulingExecutionContext, asset_slice: AssetSlice
    ) -> AssetSlice:
        return asset_slice.latest_complete_time_window

    @staticmethod
    def any_parent_updated(
        context: SchedulingExecutionContext, current_slice: AssetSlice
    ) -> AssetSlice:
        pks = set()
        updated_parent_space = current_slice.compute_updated_parent_slices()
        for (
            pk,
            updated_parent_slice,
        ) in updated_parent_space.parent_slices_by_partition_key.items():
            if not updated_parent_slice.is_empty:
                pks.add(pk)

        return context.slice_factory.from_partition_keys(current_slice.asset_key, pks)

    @staticmethod
    def all_parents_updated(
        context: SchedulingExecutionContext, current_slice: AssetSlice
    ) -> AssetSlice:
        pks = set()
        updated_parent_space = current_slice.compute_updated_parent_slices()
        for pk, updated_parent_slice in updated_parent_space.parent_slices_by_partition_key.items():
            parent_slice = current_slice.compute_parent_slice_of_partition_key(
                updated_parent_slice.asset_key, pk
            )
            if updated_parent_slice.equals(parent_slice):
                pks.add(pk)
        return context.slice_factory.from_partition_keys(current_slice.asset_key, pks)

    @staticmethod
    def unsynced(context: SchedulingExecutionContext, current_slice: AssetSlice) -> AssetSlice:
        return current_slice.compute_unsynced()

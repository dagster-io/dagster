import itertools
from typing import NamedTuple, Sequence

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
    candidate_partition_space = upstream_of_starting_space.for_keys(
        upstream_of_starting_space.root_asset_keys
    )

    launch_partition_space = PartitionSpace.empty(context.asset_graph_view)

    # now that we have the partition space we descend downward to filter

    for asset_key in itertools.chain(*context.asset_graph.toposort_asset_keys()):
        candidate_slice = candidate_partition_space.get_asset_slice(asset_key)
        asset_info = context.get_scheduling_info(asset_key)
        evaluation_result = (
            asset_info.scheduling_policy.evaluate(context, candidate_slice)
            if asset_info.scheduling_policy
            else EvaluationResult(asset_slice=context.slice_factory.empty(asset_key))
        )

        launch_partition_space = launch_partition_space.with_asset_slice(
            evaluation_result.asset_slice
        )

        # explore one level downward in the candidate partition space
        for child_asset_key in context.asset_graph.get_children(asset_key):
            candidate_partition_space = candidate_partition_space.with_asset_slice(
                context.asset_graph_view.child_asset_slice(child_asset_key, candidate_slice)
            )

    tags = {}

    partition_backfill = PartitionBackfill.from_asset_graph_subset(
        backfill_id=backfill_id,
        asset_graph_subset=launch_partition_space.asset_graph_subset,
        backfill_timestamp=context.tick_dt.timestamp(),
        tags=tags,
        dynamic_partitions_store=context.queryer,
    )

    return ReactiveSchedulingPlan(
        partition_backfill=partition_backfill,
        launch_partition_space=launch_partition_space,
        candidate_partition_space=candidate_partition_space,
    )


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


# Language
# * Out of sync: Assets are out of sync if they have a new code version or new upstream data version, or
# if their parents within zone # of control are out of sync
# * Updated: Asset has a new materialization with a new data version relative to current materialized data version


class OnAnyNewParentUpdated(SchedulingPolicy):
    def evaluate(
        self, context: SchedulingExecutionContext, current_slice: AssetSlice
    ) -> EvaluationResult:
        return EvaluationResult(asset_slice=Rules.any_parent_updated(context, current_slice))


class AnyParentOutOfSync(SchedulingPolicy):
    def evaluate(
        self, context: SchedulingExecutionContext, current_slice: AssetSlice
    ) -> EvaluationResult:
        return EvaluationResult(asset_slice=Rules.any_parent_out_of_sync(context, current_slice))


class AllParentsOutOfSync(SchedulingPolicy):
    def evaluate(
        self, context: SchedulingExecutionContext, current_slice: AssetSlice
    ) -> EvaluationResult:
        return EvaluationResult(asset_slice=Rules.all_parents_out_of_sync(context, current_slice))


class DefaultSchedulingPolicy(SchedulingPolicy):
    def evaluate(
        self, context: SchedulingExecutionContext, current_slice: AssetSlice
    ) -> EvaluationResult:
        return EvaluationResult(
            asset_slice=Rules.any_parent_updated(
                context, Rules.latest_time_window(context, current_slice)
            )
        )


class Rules:
    @staticmethod
    def latest_time_window(
        context: SchedulingExecutionContext, asset_slice: AssetSlice
    ) -> AssetSlice:
        return asset_slice.latest_complete_time_window

    @staticmethod
    def any_parent_updated(
        context: SchedulingExecutionContext, current_slice: AssetSlice
    ) -> AssetSlice:
        return (
            context.empty_slice(current_slice.asset_key)
            if current_slice.updated_parent_partition_space.is_empty
            else current_slice
        )

    @staticmethod
    def all_parents_updated(
        context: SchedulingExecutionContext, current_slice: AssetSlice
    ) -> AssetSlice:
        return (
            current_slice
            if current_slice.updated_parent_partition_space == current_slice.parent_parition_space
            else context.empty_slice(current_slice.asset_key)
        )

    @staticmethod
    def any_parent_out_of_sync(
        context: SchedulingExecutionContext, current_slice: AssetSlice
    ) -> AssetSlice:
        return (
            context.empty_slice(current_slice.asset_key)
            if current_slice.unsynced_parent_partition_space.is_empty
            else current_slice
        )

    @staticmethod
    def all_parents_out_of_sync(
        context: SchedulingExecutionContext, current_slice: AssetSlice
    ) -> AssetSlice:
        return (
            current_slice
            if current_slice.unsynced_parent_partition_space == current_slice.parent_parition_space
            else context.empty_slice(current_slice.asset_key)
        )

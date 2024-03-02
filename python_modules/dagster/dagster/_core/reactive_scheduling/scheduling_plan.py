import itertools
from typing import NamedTuple, Sequence

from dagster import _check as check
from dagster._core.definitions.asset_subset import ValidAssetSubset
from dagster._core.definitions.partition import StaticPartitionsDefinition
from dagster._core.definitions.time_window_partitions import (
    TimeWindowPartitionsDefinition,
)
from dagster._core.execution.backfill import PartitionBackfill
from dagster._core.reactive_scheduling.scheduling_policy import (
    EvaluationResult,
    SchedulingExecutionContext,
    SchedulingPolicy,
)
from dagster._core.utils import make_new_backfill_id

from .asset_graph_traverser import AssetSubsetFactory, PartitionSpace


class ReactiveSchedulingPlan(NamedTuple):
    candidate_partition_space: PartitionSpace
    launch_partition_space: PartitionSpace
    partition_backfill: PartitionBackfill


def build_reactive_scheduling_plan(
    context: SchedulingExecutionContext, starting_subsets: Sequence[ValidAssetSubset]
) -> ReactiveSchedulingPlan:
    # todos/questions:
    # * should the starting subset always be unconditionally included? or should it respect evaluation?
    backfill_id = make_new_backfill_id()

    upstream_of_starting_space = create_partition_space_upstream_of_subsets(
        context, starting_subsets
    )

    # candidates start at the root
    candidate_partition_space = upstream_of_starting_space.for_keys(
        upstream_of_starting_space.root_asset_keys
    )

    launch_partition_space = PartitionSpace.empty(context.asset_graph)

    # now that we have the partition space we descend downward to filter

    for asset_key in itertools.chain(*context.asset_graph.toposort_asset_keys()):
        candidate_subset = candidate_partition_space.get_asset_subset(asset_key)
        asset_info = context.get_scheduling_info(asset_key)
        evaluation_result = (
            asset_info.scheduling_policy.evaluate(context, candidate_subset)
            if asset_info.scheduling_policy
            else EvaluationResult(
                asset_subset=ValidAssetSubset.empty(asset_key, asset_info.partitions_def)
            )
        )

        launch_partition_space = launch_partition_space.with_asset_subset(
            evaluation_result.asset_subset
        )

        # explore one level downward in the candidate partition space
        for child_asset_key in context.asset_graph.get_children(asset_key):
            candidate_partition_space = candidate_partition_space.with_asset_subset(
                context.traverser.child_asset_subset(child_asset_key, candidate_subset)
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


def create_partition_space_upstream_of_subsets(
    context: SchedulingExecutionContext, starting_subsets: Sequence[ValidAssetSubset]
) -> PartitionSpace:
    upstream_of_starting_space = PartitionSpace.empty(context.asset_graph)

    for starting_subset in starting_subsets:
        upstream_of_starting_space = upstream_of_starting_space.with_partition_space(
            context.traverser.create_upstream_partition_space(starting_subset)
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
        self, context: SchedulingExecutionContext, current_subset: ValidAssetSubset
    ) -> EvaluationResult:
        return EvaluationResult(asset_subset=Rules.any_parent_updated(context, current_subset))


class AnyParentOutOfSync(SchedulingPolicy):
    def evaluate(
        self, context: SchedulingExecutionContext, current_subset: ValidAssetSubset
    ) -> EvaluationResult:
        return EvaluationResult(asset_subset=Rules.any_parent_out_of_sync(context, current_subset))


class AllParentsOutOfSync(SchedulingPolicy):
    def evaluate(
        self, context: SchedulingExecutionContext, current_subset: ValidAssetSubset
    ) -> EvaluationResult:
        return EvaluationResult(asset_subset=Rules.all_parents_out_of_sync(context, current_subset))


class DefaultSchedulingPolicy(SchedulingPolicy):
    def evaluate(
        self, context: SchedulingExecutionContext, current_subset: ValidAssetSubset
    ) -> EvaluationResult:
        return EvaluationResult(
            asset_subset=Rules.any_parent_updated(
                context, Rules.latest_time_window(context, current_subset)
            )
        )


class Rules:
    @staticmethod
    def latest_time_window(
        context: SchedulingExecutionContext, asset_subset: ValidAssetSubset
    ) -> ValidAssetSubset:
        partitions_def = context.asset_graph.get_assets_def(asset_subset.asset_key).partitions_def
        if partitions_def is None:
            return asset_subset

        if isinstance(partitions_def, StaticPartitionsDefinition):
            return asset_subset

        if isinstance(partitions_def, TimeWindowPartitionsDefinition):
            time_window = partitions_def.get_last_partition_window(context.tick_dt)
            return (
                AssetSubsetFactory.from_time_window(
                    context.asset_graph, asset_subset.asset_key, time_window
                )
                if time_window
                else context.empty_subset(asset_subset.asset_key)
            )

        check.failed(f"Unsupported partitions_def: {partitions_def}")

    @staticmethod
    def any_parent_updated(
        context: SchedulingExecutionContext, current_subset: ValidAssetSubset
    ) -> ValidAssetSubset:
        updated_parent_partition_space = context.traverser.get_updated_parent_partition_space(
            current_subset
        )
        return (
            context.empty_subset(current_subset.asset_key)
            if updated_parent_partition_space.is_empty
            else current_subset
        )

    @staticmethod
    def all_parents_updated(
        context: SchedulingExecutionContext, current_subset: ValidAssetSubset
    ) -> ValidAssetSubset:
        updated_parent_space = context.traverser.get_updated_parent_partition_space(current_subset)
        parent_space = context.traverser.get_parent_partition_space(current_subset)
        return (
            current_subset
            if updated_parent_space == parent_space
            else context.empty_subset(current_subset.asset_key)
        )

    @staticmethod
    def any_parent_out_of_sync(
        context: SchedulingExecutionContext, current_subset: ValidAssetSubset
    ) -> ValidAssetSubset:
        unsynced_parent_space = context.traverser.get_unsynced_parent_partition_space(
            current_subset
        )
        return (
            context.empty_subset(current_subset.asset_key)
            if unsynced_parent_space.is_empty
            else current_subset
        )

    @staticmethod
    def all_parents_out_of_sync(
        context: SchedulingExecutionContext, current_subset: ValidAssetSubset
    ) -> ValidAssetSubset:
        unsynced_parent_space = context.traverser.get_unsynced_parent_partition_space(
            current_subset
        )
        parent_space = context.traverser.get_parent_partition_space(current_subset)
        return (
            current_subset
            if unsynced_parent_space == parent_space
            else context.empty_subset(current_subset.asset_key)
        )

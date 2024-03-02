import itertools
from typing import NamedTuple, Sequence

from dagster._core.definitions.asset_subset import ValidAssetSubset
from dagster._core.execution.backfill import PartitionBackfill
from dagster._core.reactive_scheduling.scheduling_policy import (
    EvaluationResult,
    SchedulingExecutionContext,
)
from dagster._core.utils import make_new_backfill_id

from .asset_graph_traverser import PartitionSpace


class ReactiveSchedulingPlan(NamedTuple):
    candidate_partition_space: PartitionSpace
    launch_partition_space: PartitionSpace
    partition_backfill: PartitionBackfill


def build_reactive_scheduling_plan(
    context: SchedulingExecutionContext, starting_subsets: Sequence[ValidAssetSubset]
) -> ReactiveSchedulingPlan:
    backfill_id = make_new_backfill_id()

    upstream_of_starting_space = create_partition_space_upstream_of_subsets(
        context, starting_subsets
    )

    # now that we have the partition space we descend downward to filter

    # candidates start at the root
    candidate_partition_space = upstream_of_starting_space.for_keys(
        upstream_of_starting_space.root_asset_keys
    )
    launch_partition_space = PartitionSpace.empty(context.asset_graph)

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

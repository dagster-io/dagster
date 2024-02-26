from datetime import datetime
from typing import Optional, Set

from dagster import _check as check
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetKey, CoercibleToAssetKey
from dagster._core.instance import DagsterInstance
from dagster._core.reactive_scheduling.reactive_scheduling_plan import (
    PulseResult,
    ReactiveSchedulingGraph,
    default_partition_keys,
    pulse_policy_on_asset,
)
from dagster._core.reactive_scheduling.scheduling_policy import (
    AssetPartition,
    RequestReaction,
    SchedulingExecutionContext,
    SchedulingPolicy,
    SchedulingResult,
)
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer


def run_scheduling_pulse_on_asset(
    defs: Definitions,
    asset_key: CoercibleToAssetKey,
    instance: Optional[DagsterInstance] = None,
    evaluation_dt: Optional[datetime] = None,
    previous_dt: Optional[datetime] = None,
    previous_cursor: Optional[str] = None,
) -> PulseResult:
    return pulse_policy_on_asset(
        asset_key=AssetKey.from_coercible(asset_key),
        repository_def=defs.get_repository_def(),
        queryer=CachingInstanceQueryer(instance, defs.get_repository_def().asset_graph)
        if instance
        else CachingInstanceQueryer.ephemeral(defs),
        tick_dt=evaluation_dt or datetime.now(),
        previous_tick_dt=previous_dt,
        previous_cursor=previous_cursor,
    )


class AlwaysLaunchSchedulingPolicy(SchedulingPolicy):
    def schedule(self, context: SchedulingExecutionContext) -> SchedulingResult:
        return SchedulingResult(launch=True)


def default_asset_partitions(
    context: SchedulingExecutionContext, asset_key: AssetKey
) -> Set[AssetPartition]:
    assets_def = context.repository_def.asset_graph.get_assets_def(context.ticked_asset_key)
    if not assets_def.partitions_def:
        return {AssetPartition(asset_key)}
    else:
        return {
            AssetPartition(asset_key, partition_key)
            for partition_key in check.not_none(default_partition_keys(assets_def.partitions_def))
        }


class AlwaysDeferSchedulingPolicy(SchedulingPolicy):
    def schedule(self, context: SchedulingExecutionContext) -> SchedulingResult:
        return SchedulingResult(launch=False)

    def react_to_downstream_request(
        self, context: SchedulingExecutionContext, asset_partition: AssetPartition
    ) -> RequestReaction:
        return RequestReaction(include=True)

    def react_to_upstream_request(
        self, context: SchedulingExecutionContext, asset_partition: AssetPartition
    ) -> RequestReaction:
        return RequestReaction(include=True)


def any_parent_out_of_sync(
    context: SchedulingExecutionContext, asset_partition: AssetPartition
) -> bool:
    scheduling_graph = ReactiveSchedulingGraph.from_context(context)

    parent_partitions = scheduling_graph.get_all_parent_partitions(
        asset_partition=asset_partition,
    )

    return bool(
        context.queryer.get_parent_asset_partitions_updated_after_child(
            asset_partition=asset_partition,
            parent_asset_partitions=parent_partitions,
            respect_materialization_data_versions=True,
            ignored_parent_keys=set(),
        )
    )


def all_parents_out_of_sync(
    context: SchedulingExecutionContext, asset_partition: AssetPartition
) -> bool:
    scheduling_graph = ReactiveSchedulingGraph.from_context(context)

    parent_partitions = scheduling_graph.get_all_parent_partitions(
        asset_partition=asset_partition,
    )

    updated_parent_partitions = context.queryer.get_parent_asset_partitions_updated_after_child(
        asset_partition=asset_partition,
        parent_asset_partitions=parent_partitions,
        respect_materialization_data_versions=True,
        ignored_parent_keys=set(),
    )

    return updated_parent_partitions == parent_partitions


class IncludeOnAnyParentOutOfSync(SchedulingPolicy):
    def react_to_downstream_request(
        self, context: SchedulingExecutionContext, asset_partition: AssetPartition
    ) -> RequestReaction:
        return RequestReaction(any_parent_out_of_sync(context, asset_partition))

    def react_to_upstream_request(
        self, context: SchedulingExecutionContext, asset_partition: AssetPartition
    ) -> RequestReaction:
        # upstream demands request overrides any updating behavior
        # note: is this true?
        # TODO: what about getting the other upstreams?
        return RequestReaction(include=True)


class IncludeOnAllParentsOutOfSync(SchedulingPolicy):
    def react_to_downstream_request(
        self, context: SchedulingExecutionContext, asset_partition: AssetPartition
    ) -> RequestReaction:
        # here we respect upstream versioning to see if we actually need this
        return RequestReaction(all_parents_out_of_sync(context, asset_partition))

    def react_to_upstream_request(
        self, context: SchedulingExecutionContext, asset_partition: AssetPartition
    ) -> RequestReaction:
        # upstream demands request overrides any updating behavior
        # note: is this true?
        # TODO: what about getting the other upstreams?
        return RequestReaction(include=True)

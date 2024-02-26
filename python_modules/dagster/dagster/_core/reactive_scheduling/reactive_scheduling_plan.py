import datetime
from typing import List, NamedTuple, Optional, Set

from dagster import (
    _check as check,
)
from dagster._core.definitions.asset_daemon_context import build_run_requests
from dagster._core.definitions.asset_subset import AssetSubset, ValidAssetSubset
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.internal_asset_graph import InternalAssetGraph
from dagster._core.definitions.partition import (
    PartitionsDefinition,
)
from dagster._core.definitions.repository_definition.repository_definition import (
    RepositoryDefinition,
)
from dagster._core.definitions.run_request import RunRequest
from dagster._core.instance import DagsterInstance
from dagster._core.reactive_scheduling.scheduling_policy import (
    AssetPartition,
    SchedulingExecutionContext,
    SchedulingPolicy,
    SchedulingResult,
)
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer


class ReactiveAssetInfo(NamedTuple):
    asset_key: AssetKey
    scheduling_policy: SchedulingPolicy
    partitions_def: Optional[PartitionsDefinition]


class ReactiveSchedulingGraph(NamedTuple):
    queryer: CachingInstanceQueryer
    repository_def: RepositoryDefinition
    tick_dt: datetime.datetime

    @property
    def instance(self) -> DagsterInstance:
        return self.queryer.instance

    @staticmethod
    def from_context(context: SchedulingExecutionContext):
        return ReactiveSchedulingGraph(
            queryer=context.queryer,
            repository_def=context.repository_def,
            tick_dt=context.tick_dt,
        )

    @property
    def asset_graph(self) -> InternalAssetGraph:
        return self.repository_def.asset_graph

    def get_required_asset_info(self, asset_key: AssetKey) -> ReactiveAssetInfo:
        return check.not_none(self.get_asset_info(asset_key))

    def get_asset_info(self, asset_key: AssetKey) -> Optional[ReactiveAssetInfo]:
        assets_def = self.asset_graph.get_assets_def(asset_key)
        return (
            ReactiveAssetInfo(
                asset_key=asset_key,
                scheduling_policy=assets_def.scheduling_policies_by_key[asset_key],
                partitions_def=assets_def.partitions_def,
            )
            if asset_key in assets_def.scheduling_policies_by_key
            else None
        )

    def make_valid_subset(
        self,
        asset_key: AssetKey,
        asset_partitions: Optional[Set[AssetPartition]] = None,
    ) -> ValidAssetSubset:
        asset_info = self.get_asset_info(asset_key)
        assert asset_info
        if asset_partitions is not None:
            # explicit partitions. do as you are told
            check.invariant(
                asset_info.partitions_def is not None,
                "If you pass in asset_partitions it must be partitioned asset",
            )
            return AssetSubset.from_asset_partitions_set(
                asset_key=asset_key,
                asset_partitions_set=asset_partitions,
                partitions_def=asset_info.partitions_def,
            )
        else:
            # I think this business logic should be farther up the stack really
            if asset_info.partitions_def is None:
                return AssetSubset(asset_key, True).as_valid(asset_info.partitions_def)
            else:
                return AssetSubset.all(
                    asset_key,
                    asset_info.partitions_def,
                    self.instance,
                    current_time=self.tick_dt,
                )

    def get_parent_asset_subset(
        self, asset_subset: ValidAssetSubset, parent_asset_key: AssetKey
    ) -> ValidAssetSubset:
        parent_assets_def = self.repository_def.assets_defs_by_key[parent_asset_key]
        return self.asset_graph.get_parent_asset_subset(
            child_asset_subset=asset_subset,
            parent_asset_key=parent_asset_key,
            dynamic_partitions_store=self.instance,
            current_time=self.tick_dt,
        ).as_valid(parent_assets_def.partitions_def)

    def get_child_asset_subset(
        self, asset_subset: ValidAssetSubset, child_asset_key: AssetKey
    ) -> ValidAssetSubset:
        child_assets_def = self.repository_def.assets_defs_by_key[child_asset_key]
        return self.asset_graph.get_child_asset_subset(
            parent_asset_subset=asset_subset,
            child_asset_key=child_asset_key,
            dynamic_partitions_store=self.instance,
            current_time=self.tick_dt,
        ).as_valid(child_assets_def.partitions_def)


class ReactionSchedulingPlan(NamedTuple):
    # computed requested partitions
    requested_partitions: Set[AssetPartition]


def make_asset_partitions(ak: AssetKey, partition_keys: Set[str]) -> Set[AssetPartition]:
    return {AssetPartition(ak, partition_key) for partition_key in partition_keys}


def build_reactive_scheduling_plan(
    context: SchedulingExecutionContext,
    scheduling_graph: ReactiveSchedulingGraph,
    starting_key: AssetKey,  # starting asset key
    scheduling_result: SchedulingResult,
) -> ReactionSchedulingPlan:
    starting_subset = scheduling_graph.make_valid_subset(
        starting_key,
        (
            None
            if scheduling_result.partition_keys is None
            else make_asset_partitions(starting_key, scheduling_result.partition_keys)
        ),
    )

    upward_requested_partitions = ascending_scheduling_pulse(
        context, scheduling_graph, starting_subset
    )
    downward_requested_partitions = descending_scheduling_pulse(
        context, scheduling_graph, starting_subset
    )
    return ReactionSchedulingPlan(
        requested_partitions=upward_requested_partitions | downward_requested_partitions
    )


def ascending_scheduling_pulse(
    context: SchedulingExecutionContext,
    graph: ReactiveSchedulingGraph,
    starting_subset: ValidAssetSubset,
) -> Set[AssetPartition]:
    visited: Set[AssetPartition] = set()
    to_execute: Set[AssetPartition] = set()

    def _ascend(current: ValidAssetSubset):
        to_execute.update(current.asset_partitions)
        visited.update(current.asset_partitions)

        for parent_asset_key in graph.asset_graph.get_parents(current.asset_key):
            parent_info = graph.get_asset_info(parent_asset_key)
            if not parent_info:
                continue

            parent_subset = graph.get_parent_asset_subset(current, parent_asset_key)
            requested_subset = _compute_requested_upstream_subset(parent_info, parent_subset)

            if requested_subset.asset_partitions:
                _ascend(requested_subset)

    def _compute_requested_upstream_subset(
        parent_info: ReactiveAssetInfo, parent_subset: ValidAssetSubset
    ) -> ValidAssetSubset:
        included: Set[AssetPartition] = set()
        for asset_partition in parent_subset.asset_partitions:
            parent_reaction = parent_info.scheduling_policy.react_to_downstream_request(
                context, asset_partition
            )
            if parent_reaction.include and asset_partition not in visited:
                included.add(asset_partition)

        return graph.make_valid_subset(parent_info.asset_key, included)

    _ascend(starting_subset)

    return to_execute


def descending_scheduling_pulse(
    context: SchedulingExecutionContext,
    graph: ReactiveSchedulingGraph,
    starting_subset: ValidAssetSubset,
) -> Set[AssetPartition]:
    visited: Set[AssetPartition] = set()
    to_execute: Set[AssetPartition] = set()

    def _descend(current: ValidAssetSubset):
        to_execute.update(current.asset_partitions)
        visited.update(current.asset_partitions)

        for child_asset_key in graph.asset_graph.get_children(current.asset_key):
            child_info = graph.get_asset_info(child_asset_key)
            if not child_info:
                continue

            child_subset = graph.get_child_asset_subset(current, child_asset_key)
            requested_subset = _compute_requested_downstream_subset(child_info, child_subset)

            if requested_subset.asset_partitions:
                _descend(requested_subset)

    def _compute_requested_downstream_subset(
        child_info: ReactiveAssetInfo, child_subset: ValidAssetSubset
    ) -> ValidAssetSubset:
        included: Set[AssetPartition] = set()
        for asset_partition in child_subset.asset_partitions:
            child_reaction = child_info.scheduling_policy.react_to_upstream_request(
                context, asset_partition
            )
            if child_reaction.include and asset_partition not in visited:
                included.add(asset_partition)

        requested_subset = graph.make_valid_subset(child_info.asset_key, included)
        return requested_subset

    _descend(starting_subset)

    return to_execute


class PulseResult(NamedTuple):
    run_requests: List[RunRequest]
    scheduling_result: Optional[SchedulingResult]


def pulse_policy_on_asset(
    asset_key: AssetKey,
    repository_def: RepositoryDefinition,
    previous_tick_dt: Optional[datetime.datetime],
    tick_dt: datetime.datetime,
    queryer: CachingInstanceQueryer,
    previous_cursor: Optional[str],
) -> PulseResult:
    scheduling_graph = ReactiveSchedulingGraph(
        repository_def=repository_def,
        queryer=queryer,
        tick_dt=tick_dt,
    )
    asset_info = scheduling_graph.get_asset_info(asset_key)
    if not asset_info:
        return PulseResult(run_requests=[], scheduling_result=None)

    context = SchedulingExecutionContext(
        repository_def=repository_def,
        queryer=queryer,
        tick_dt=tick_dt,
        asset_key=asset_key,
        previous_tick_dt=previous_tick_dt,
        previous_cursor=previous_cursor,
    )

    scheduling_result = asset_info.scheduling_policy.schedule(context)

    check.invariant(scheduling_result, "Scheduling policy must return a SchedulingResult")

    if not scheduling_result.launch:
        return PulseResult(run_requests=[], scheduling_result=scheduling_result)

    scheduling_plan = build_reactive_scheduling_plan(
        context=context,
        scheduling_graph=scheduling_graph,
        starting_key=asset_key,
        scheduling_result=scheduling_result,
    )

    return PulseResult(
        list(
            build_run_requests(
                asset_partitions=scheduling_plan.requested_partitions,
                asset_graph=scheduling_graph.asset_graph,
                run_tags={},
            )
        ),
        scheduling_result,
    )

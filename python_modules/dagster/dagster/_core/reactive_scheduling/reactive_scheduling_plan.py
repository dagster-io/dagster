import datetime
from typing import AbstractSet, List, NamedTuple, Optional, Set

from dagster import (
    _check as check,
)
from dagster._core.definitions.asset_daemon_context import build_run_requests
from dagster._core.definitions.asset_subset import AssetSubset, ValidAssetSubset
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.internal_asset_graph import InternalAssetGraph
from dagster._core.definitions.partition import (
    AllPartitionsSubset,
    PartitionsDefinition,
    StaticPartitionsDefinition,
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


class AssetPartitionRange:
    __slots__ = ["_asset_subset"]

    def __init__(self, asset_subset: ValidAssetSubset):
        self._asset_subset = asset_subset

    @property
    def asset_partitions(self) -> AbstractSet[AssetPartition]:
        return self._asset_subset.asset_partitions

    @property
    def is_complete(self) -> bool:
        return (
            self._asset_subset.bool_value
            if self._asset_subset.is_partitioned
            else isinstance(self._asset_subset.value, AllPartitionsSubset)
        )


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

    def get_all_parent_partitions(
        self, asset_partition: AssetPartition
    ) -> AbstractSet[AssetPartition]:
        return self.asset_graph.get_parents_partitions(
            dynamic_partitions_store=self.queryer,
            current_time=self.tick_dt,
            asset_key=asset_partition.asset_key,
            partition_key=asset_partition.partition_key,
        ).parent_partitions

    def make_valid_unpartitioned_subset(
        self, asset_key: AssetKey, selected: bool
    ) -> ValidAssetSubset:
        asset_info = self.get_required_asset_info(asset_key)
        check.invariant(asset_info.partitions_def is None, "Asset must be unpartitioned")
        return AssetSubset(asset_key, selected).as_valid(partitions_def=None)

    def make_valid_partitioned_subset(
        self, asset_key: AssetKey, partition_keys: Set[str]
    ) -> ValidAssetSubset:
        asset_info = self.get_required_asset_info(asset_key)
        check.invariant(asset_info.partitions_def, "Asset must be partitioned")
        return AssetSubset.from_asset_partitions_set(
            asset_key=asset_key,
            asset_partitions_set={
                AssetPartition(asset_key, partition_key) for partition_key in partition_keys
            },
            partitions_def=asset_info.partitions_def,
        )

    def make_valid_subset(
        self, asset_info: ReactiveAssetInfo, partition_keys: Optional[Set[str]]
    ) -> ValidAssetSubset:
        if asset_info.partitions_def:
            assert partition_keys is not None
            return self.make_valid_partitioned_subset(
                asset_key=asset_info.asset_key,
                # better logic for defaults here
                partition_keys=partition_keys,
            )
        else:
            check.invariant(partition_keys is None)
            return self.make_valid_unpartitioned_subset(
                asset_key=asset_info.asset_key, selected=True
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
    starting_subset: ValidAssetSubset,
) -> ReactionSchedulingPlan:
    upward_requested_partitions = ascending_scheduling_pulse(
        context, scheduling_graph, starting_subset
    )
    downward_requested_partitions = descending_scheduling_pulse(
        context, scheduling_graph, starting_subset
    )
    return ReactionSchedulingPlan(
        requested_partitions=(
            upward_requested_partitions
            | downward_requested_partitions
            | starting_subset.asset_partitions
        )
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

        return make_valid_subset_from_included(graph, parent_info, included)

    _ascend(starting_subset)

    return to_execute


def make_valid_subset_from_included(
    graph: ReactiveSchedulingGraph, asset_info: ReactiveAssetInfo, included: Set[AssetPartition]
) -> ValidAssetSubset:
    if asset_info.partitions_def:
        return graph.make_valid_partitioned_subset(
            asset_info.asset_key, {check.not_none(ap.partition_key) for ap in included}
        )
    else:
        return graph.make_valid_unpartitioned_subset(asset_info.asset_key, bool(included))


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

        return make_valid_subset_from_included(graph, child_info, included)

    _descend(starting_subset)

    return to_execute


class PulseResult(NamedTuple):
    run_requests: List[RunRequest]
    scheduling_result: Optional[SchedulingResult]


# TODO incorporate time for time-partitioned assets
# get_new_asset_partitions_to_request has this logic
def default_partition_keys(partitions_def: Optional[PartitionsDefinition]) -> Optional[Set[str]]:
    if not partitions_def:
        return None

    if isinstance(partitions_def, StaticPartitionsDefinition):
        return set(partitions_def.get_partition_keys())
    else:
        last_partition_key = partitions_def.get_last_partition_key()
        return {last_partition_key} if last_partition_key else set()


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

    starting_subset = scheduling_graph.make_valid_subset(
        asset_info,
        scheduling_result.explicit_partition_keys
        or default_partition_keys(asset_info.partitions_def),
    )

    scheduling_plan = build_reactive_scheduling_plan(
        context=context,
        scheduling_graph=scheduling_graph,
        starting_subset=starting_subset,
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


def make_valid_asset_subset(
    scheduling_graph: ReactiveSchedulingGraph,
    asset_info: ReactiveAssetInfo,
    partition_keys: Optional[Set[str]],
) -> ValidAssetSubset:
    if asset_info.partitions_def:
        starting_subset = scheduling_graph.make_valid_partitioned_subset(
            asset_key=asset_info.asset_key,
            # better logic for defaults here
            partition_keys=partition_keys or default_partition_keys(asset_info.partitions_def),
        )
    else:
        check.invariant(partition_keys is None)
        starting_subset = scheduling_graph.make_valid_unpartitioned_subset(
            asset_key=asset_info.asset_key, selected=True
        )

    return starting_subset

from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Dict,
    FrozenSet,
    Iterable,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
)
from dagster._utils.cached_method import cached_method

import pendulum

import dagster._check as check
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.freshness_based_auto_materialize import (
    determine_asset_partitions_to_auto_materialize_for_freshness,
)
from dagster._core.definitions.run_request import RunRequest
from dagster._core.definitions.time_window_partitions import (
    get_time_partitions_def,
)

from .asset_daemon_cursor import AssetDaemonCursor
from .asset_graph import AssetGraph
from .auto_materialize_condition import (
    AutoMaterializeAssetEvaluation,
    AutoMaterializeCondition,
    AutoMaterializeDecisionType,
    MaxMaterializationsExceededAutoMaterializeCondition,
    MissingAutoMaterializeCondition,
    ParentMaterializedAutoMaterializeCondition,
    ParentOutdatedAutoMaterializeCondition,
)
from .partition import (
    PartitionsDefinition,
    ScheduleType,
)

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance
    from dagster._utils.caching_instance_queryer import CachingInstanceQueryer  # expensive import


def _will_materialize_for_conditions(
    conditions: Optional[AbstractSet[AutoMaterializeCondition]],
) -> bool:
    """Based on a set of conditions, determine if the asset will be materialized."""
    return (
        AutoMaterializeDecisionType.from_conditions(conditions)
        == AutoMaterializeDecisionType.MATERIALIZE
    )


class AssetDaemonIteration:
    def __init__(
        self,
        instance: "DagsterInstance",
        asset_graph: AssetGraph,
        stored_cursor: AssetDaemonCursor,
        target_asset_keys: Optional[AbstractSet[AssetKey]] = None,
    ):
        from dagster._utils.caching_instance_queryer import (
            CachingInstanceQueryer,
        )

        self._instance_queryer = CachingInstanceQueryer(instance, asset_graph)
        self._stored_cursor = stored_cursor
        self._auto_materialize_asset_keys = target_asset_keys or {
            key
            for key, policy in self.asset_graph.auto_materialize_policies_by_key.items()
            if policy is not None
        }

        # fetch some data in advance to batch some queries
        self.instance_queryer.prefetch_asset_records(
            [
                key
                for key in self.auto_materialize_asset_keys_and_parents
                if not self.asset_graph.is_source(key)
            ]
        )
        self.instance_queryer.prefetch_asset_partition_counts(
            [
                key
                for key in self.auto_materialize_asset_keys_and_parents
                if self.asset_graph.is_partitioned(key) and not self.asset_graph.is_source(key)
            ],
            after_cursor=stored_cursor.latest_storage_id,
        )

    @property
    def instance_queryer(self) -> "CachingInstanceQueryer":
        return self._instance_queryer

    @property
    def stored_cursor(self) -> AssetDaemonCursor:
        return self._stored_cursor

    @property
    def asset_graph(self) -> AssetGraph:
        return self.instance_queryer.asset_graph

    @property
    def stored_latest_storage_id(self) -> Optional[int]:
        return self.stored_cursor.latest_storage_id

    @property
    def auto_materialize_asset_keys(self) -> AbstractSet[AssetKey]:
        return self._auto_materialize_asset_keys

    @property
    def auto_materialize_asset_keys_and_parents(self) -> AbstractSet[AssetKey]:
        return {
            parent
            for asset_key in self.auto_materialize_asset_keys
            for parent in self.asset_graph.get_parents(asset_key)
        } | self.auto_materialize_asset_keys

    @property
    def new_latest_storage_id(self) -> Optional[int]:
        (_, new_latest_storage_id) = self._cached()
        return new_latest_storage_id

    @property
    def asset_partitions_with_newly_updated_parents(self) -> AbstractSet[AssetKeyPartitionKey]:
        (asset_partitions_with_newly_updated_parents, _) = self._cached()
        return asset_partitions_with_newly_updated_parents

    @property
    def newly_handled_asset_partitions(self) -> AbstractSet[AssetKeyPartitionKey]:
        (_, newly_handled_asset_partitions) = self._cached2()
        return newly_handled_asset_partitions

    @property
    def unhandled_asset_partitions(self) -> AbstractSet[AssetKeyPartitionKey]:
        (unhandled_asset_partitions, _) = self._cached2()
        return unhandled_asset_partitions

    @cached_method
    def _cached(self) -> Tuple[AbstractSet[AssetKeyPartitionKey], Optional[int]]:
        return self.instance_queryer.asset_partitions_with_newly_updated_parents(
            after_cursor=self.stored_cursor.latest_storage_id,
            target_asset_keys=self.auto_materialize_asset_keys,
            target_asset_keys_and_parents=self.auto_materialize_asset_keys_and_parents,
        )

    @cached_method
    def _cached2(
        self,
    ) -> Tuple[AbstractSet[AssetKeyPartitionKey], AbstractSet[AssetKeyPartitionKey]]:
        """Finds asset partitions that have never been materialized, requested, or discarded and
        that have no parents.
        """
        unhandled_asset_partitions = set()
        newly_handled_asset_partitions = set()
        for asset_key in self.asset_graph.root_asset_keys & self.auto_materialize_asset_keys:
            if not self.asset_graph.is_partitioned(asset_key):
                if asset_key not in self.stored_cursor.handled_root_asset_keys:
                    asset_partition = AssetKeyPartitionKey(asset_key)
                    if self.instance_queryer.asset_partition_has_materialization_or_observation(
                        asset_partition
                    ):
                        newly_handled_asset_partitions.add(asset_partition)
                    else:
                        unhandled_asset_partitions.add(asset_partition)
            else:
                for partition_key in self.stored_cursor.get_unhandled_partitions(
                    asset_key,
                    self.asset_graph,
                    dynamic_partitions_store=self.instance_queryer,
                    current_time=self.instance_queryer.evaluation_time,
                ):
                    asset_partition = AssetKeyPartitionKey(asset_key, partition_key)
                    if self.instance_queryer.asset_partition_has_materialization_or_observation(
                        asset_partition
                    ):
                        newly_handled_asset_partitions.add(asset_partition)
                    else:
                        unhandled_asset_partitions.add(asset_partition)
        return newly_handled_asset_partitions, unhandled_asset_partitions

    def get_implicit_auto_materialize_policy(self, asset_key: AssetKey) -> AutoMaterializePolicy:
        """For backcompat with pre-auto materialize policy graphs, assume a default scope of 1 day.
        """
        auto_materialize_policy = self.asset_graph.get_auto_materialize_policy(asset_key)
        if auto_materialize_policy is None:
            time_partitions_def = get_time_partitions_def(
                self.asset_graph.get_partitions_def(asset_key)
            )
            if time_partitions_def is None:
                max_materializations_per_minute = None
            elif time_partitions_def.schedule_type == ScheduleType.HOURLY:
                max_materializations_per_minute = 24
            else:
                max_materializations_per_minute = 1
            return AutoMaterializePolicy(
                on_missing=True,
                on_new_parent_data=not bool(
                    self.asset_graph.get_downstream_freshness_policies(asset_key=asset_key)
                ),
                for_freshness=True,
                max_materializations_per_minute=max_materializations_per_minute,
            )
        return auto_materialize_policy

    def can_materialize(self, asset_partition: AssetKeyPartitionKey) -> bool:
        """A filter for eliminating asset partitions from consideration for auto-materialization."""
        return not (
            asset_partition.asset_key not in self.auto_materialize_asset_keys
            # must not be currently backfilled
            or asset_partition
            in self.instance_queryer.get_active_backfill_target_asset_graph_subset()
            # must not have invalid parent partitions
            or len(
                self.asset_graph.get_parents_partitions(
                    self.instance_queryer,
                    self.instance_queryer.evaluation_time,
                    asset_partition.asset_key,
                    asset_partition.partition_key,
                ).required_but_nonexistent_parents_partitions
            )
            > 0
        )

    def get_root_unreconciled_ancestors(
        self,
        candidate: AssetKeyPartitionKey,
        will_materialize_asset_partitions: Mapping[AssetKey, AbstractSet[AssetKeyPartitionKey]],
    ) -> FrozenSet[AssetKey]:
        """Returns the set of ancestor asset keys that must be materialized before this asset can be
        materialized.
        """
        from dagster._core.definitions.external_asset_graph import ExternalAssetGraph

        unreconciled_ancestors = set()
        for parent in self.asset_graph.get_parents_partitions(
            self.instance_queryer,
            self.instance_queryer.evaluation_time,
            candidate.asset_key,
            candidate.partition_key,
        ).parent_partitions:
            # parent will not be materialized this tick
            if not (
                parent in will_materialize_asset_partitions[parent.asset_key]
                # the parent must have the same partitioning / partition key to be materialized
                # alongside the candidate
                and self.asset_graph.have_same_partitioning(parent.asset_key, candidate.asset_key)
                and parent.partition_key == candidate.partition_key
                # the parent must be in the same repository to be materialized alongside the candidate
                and (
                    not isinstance(self.asset_graph, ExternalAssetGraph)
                    or self.asset_graph.get_repository_handle(candidate.asset_key)
                    == self.asset_graph.get_repository_handle(parent.asset_key)
                )
            ):
                unreconciled_ancestors.update(
                    self.instance_queryer.get_root_unreconciled_ancestors(asset_partition=parent)
                )
        return frozenset(unreconciled_ancestors)

    def conditions_for_candidate(
        self,
        asset_partition: AssetKeyPartitionKey,
        will_materialize_asset_partitions: Mapping[AssetKey, AbstractSet[AssetKeyPartitionKey]],
    ) -> AbstractSet[AutoMaterializeCondition]:
        auto_materialize_policy = check.not_none(
            self.get_implicit_auto_materialize_policy(asset_partition.asset_key)
        )
        conditions = set()

        # if this asset is missing
        if (
            auto_materialize_policy.on_missing
            and not self.instance_queryer.asset_partition_has_materialization_or_observation(
                asset_partition=asset_partition
            )
        ):
            conditions.add(MissingAutoMaterializeCondition())

        # if the parent has been updated
        if auto_materialize_policy.on_new_parent_data and not self.instance_queryer.is_reconciled(
            asset_partition=asset_partition
        ):
            conditions.add(ParentMaterializedAutoMaterializeCondition())

        # if the parents will not be resolved this tick
        waiting_on_asset_keys = self.get_root_unreconciled_ancestors(
            asset_partition, will_materialize_asset_partitions
        )
        if waiting_on_asset_keys:
            conditions.add(
                ParentOutdatedAutoMaterializeCondition(waiting_on_asset_keys=waiting_on_asset_keys)
            )

        if (
            # would be materialized
            _will_materialize_for_conditions(conditions)
            # has a rate limit
            and auto_materialize_policy.max_materializations_per_minute is not None
            # would exceed the rate limit
            and len(
                will_materialize_asset_partitions[asset_partition.asset_key] | {asset_partition}
            )
            > auto_materialize_policy.max_materializations_per_minute
        ):
            conditions.add(MaxMaterializationsExceededAutoMaterializeCondition())

        return conditions

    def get_conditions_by_asset_partition(
        self,
    ) -> Mapping[AssetKey, Mapping[AssetKeyPartitionKey, AbstractSet[AutoMaterializeCondition]]]:
        conditions_by_asset_partition_by_asset_key: Dict[
            AssetKey, Dict[AssetKeyPartitionKey, Set[AutoMaterializeCondition]]
        ] = defaultdict(lambda: defaultdict(set))
        will_materialize_asset_partitions: Dict[AssetKey, Set[AssetKeyPartitionKey]] = defaultdict(
            set
        )

        # first, do the freshness calculation
        for (
            asset_partition,
            conditions,
        ) in determine_asset_partitions_to_auto_materialize_for_freshness(
            data_time_resolver=CachingDataTimeResolver(instance_queryer=self.instance_queryer),
            asset_graph=self.asset_graph,
            target_asset_keys=self.auto_materialize_asset_keys,
            target_asset_keys_and_parents=self.auto_materialize_asset_keys_and_parents,
        ).items():
            conditions_by_asset_partition_by_asset_key[asset_partition.asset_key][
                asset_partition
            ] = conditions
            if _will_materialize_for_conditions(conditions):
                will_materialize_asset_partitions[asset_partition.asset_key].add(asset_partition)

        def should_reconcile(
            asset_graph: AssetGraph,
            candidates_unit: Iterable[AssetKeyPartitionKey],
            to_reconcile: AbstractSet[AssetKeyPartitionKey],
        ) -> bool:
            if any(not self.can_materialize(candidate) for candidate in candidates_unit):
                return False
            # collect all conditions that apply to any candidate in the unit
            unit_conditions = set().union(
                *(
                    self.conditions_for_candidate(candidate, will_materialize_asset_partitions)
                    for candidate in candidates_unit
                )
            )
            will_materialize = _will_materialize_for_conditions(unit_conditions)
            # for now, all candidates in the unit share the same conditions
            for candidate in candidates_unit:
                conditions_by_asset_partition_by_asset_key[candidate.asset_key][candidate].update(
                    unit_conditions
                )
                if will_materialize:
                    will_materialize_asset_partitions[candidate.asset_key].add(candidate)
            return will_materialize

        # will add conditions to the internal mapping
        self.asset_graph.bfs_filter_asset_partitions(
            self.instance_queryer,
            lambda candidates_unit, to_reconcile: should_reconcile(
                self.asset_graph, candidates_unit, to_reconcile
            ),
            {
                *self.asset_partitions_with_newly_updated_parents,
                *self.unhandled_asset_partitions,
            },
            self.instance_queryer.evaluation_time,
        )
        # filter out empty sets of conditions
        return {
            asset_key: conditions_by_asset_partition
            for asset_key, conditions_by_asset_partition in conditions_by_asset_partition_by_asset_key.items()
            if any(conditions_by_asset_partition.values())
        }

    def get_asset_keys_to_auto_observe(self, current_timestamp: float) -> AbstractSet[AssetKey]:
        assets_to_auto_observe: Set[AssetKey] = set()
        for asset_key in self.asset_graph.source_asset_keys:
            last_observe_request_timestamp = (
                self.stored_cursor.last_observe_request_timestamp_by_asset_key.get(asset_key)
            )
            auto_observe_interval_minutes = self.asset_graph.get_auto_observe_interval_minutes(
                asset_key
            )

            if auto_observe_interval_minutes and (
                last_observe_request_timestamp is None
                or (
                    last_observe_request_timestamp + auto_observe_interval_minutes * 60
                    < current_timestamp
                )
            ):
                assets_to_auto_observe.add(asset_key)
        return assets_to_auto_observe

    def evaluate(
        self,
        materialize_run_tags,
        observe_run_tags,
        auto_observe,
    ) -> Tuple[Sequence[RunRequest], AssetDaemonCursor, Sequence[AutoMaterializeAssetEvaluation]]:
        conditions_by_asset_partition_by_asset_key = self.get_conditions_by_asset_partition()

        materialize_run_requests = build_run_requests(
            asset_partitions={
                asset_partition
                for conditions_by_asset_partition in conditions_by_asset_partition_by_asset_key.values()
                for asset_partition, conditions in conditions_by_asset_partition.items()
                if _will_materialize_for_conditions(conditions)
            },
            asset_graph=self.asset_graph,
            run_tags=materialize_run_tags,
        )

        observe_request_timestamp = pendulum.now().timestamp()
        assets_to_auto_observe = (
            self.get_asset_keys_to_auto_observe(observe_request_timestamp)
            if auto_observe
            else set()
        )
        observe_run_requests = [
            RunRequest(asset_selection=list(asset_keys), tags=observe_run_tags)
            for asset_keys in self.asset_graph.split_asset_keys_by_repository(
                assets_to_auto_observe
            )
            if len(asset_keys) > 0
        ]

        return (
            [*observe_run_requests, *materialize_run_requests],
            self.stored_cursor.with_updates(
                asset_graph=self.asset_graph,
                new_latest_storage_id=self.new_latest_storage_id,
                newly_observed_source_assets=assets_to_auto_observe,
                newly_observed_source_timestamp=observe_request_timestamp,
                newly_handled_asset_partitions=self.newly_handled_asset_partitions,
                conditions_by_asset_partition_by_asset_key=conditions_by_asset_partition_by_asset_key,
            ),
            [
                AutoMaterializeAssetEvaluation.from_conditions(
                    self.asset_graph,
                    asset_key,
                    conditions_by_asset_partition,
                    self.instance_queryer,
                )
                for asset_key, conditions_by_asset_partition in conditions_by_asset_partition_by_asset_key.items()
            ],
        )


def build_run_requests(
    asset_partitions: Iterable[AssetKeyPartitionKey],
    asset_graph: AssetGraph,
    run_tags: Optional[Mapping[str, str]],
) -> Sequence[RunRequest]:
    assets_to_reconcile_by_partitions_def_partition_key: Mapping[
        Tuple[Optional[PartitionsDefinition], Optional[str]], Set[AssetKey]
    ] = defaultdict(set)

    for asset_partition in asset_partitions:
        assets_to_reconcile_by_partitions_def_partition_key[
            asset_graph.get_partitions_def(asset_partition.asset_key), asset_partition.partition_key
        ].add(asset_partition.asset_key)

    run_requests = []

    for (
        partitions_def,
        partition_key,
    ), asset_keys in assets_to_reconcile_by_partitions_def_partition_key.items():
        tags = {**(run_tags or {})}
        if partition_key is not None:
            if partitions_def is None:
                check.failed("Partition key provided for unpartitioned asset")
            tags.update({**partitions_def.get_tags_for_partition_key(partition_key)})

        for asset_keys_in_repo in asset_graph.split_asset_keys_by_repository(asset_keys):
            run_requests.append(
                # Do not call run_request.with_resolved_tags_and_config as the partition key is
                # valid and there is no config.
                # Calling with_resolved_tags_and_config is costly in asset reconciliation as it
                # checks for valid partition keys.
                RunRequest(
                    asset_selection=list(asset_keys_in_repo),
                    partition_key=partition_key,
                    tags=tags,
                )
            )

    return run_requests

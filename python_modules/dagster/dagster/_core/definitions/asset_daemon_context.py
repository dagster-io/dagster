import itertools
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
    cast,
)

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
    from dagster._core.instance import DagsterInstance, DynamicPartitionsStore
    from dagster._utils.caching_instance_queryer import CachingInstanceQueryer  # expensive import


class AssetDaemonContext:
    def __init__(
        self,
        instance: "DagsterInstance",
        asset_graph: AssetGraph,
        cursor: AssetDaemonCursor,
        materialize_run_tags: Optional[Mapping[str, str]],
        observe_run_tags: Optional[Mapping[str, str]],
        auto_observe: bool,
        target_asset_keys: Optional[AbstractSet[AssetKey]],
    ):
        from dagster._utils.caching_instance_queryer import (
            CachingInstanceQueryer,
        )

        self._instance_queryer = CachingInstanceQueryer(instance, asset_graph)
        self._cursor = cursor
        self._target_asset_keys = target_asset_keys or {
            key
            for key, policy in self.asset_graph.auto_materialize_policies_by_key.items()
            if policy is not None
        }
        self._materialize_run_tags = materialize_run_tags
        self._observe_run_tags = observe_run_tags
        self._auto_observe = auto_observe

        # fetch some data in advance to batch some queries
        self.instance_queryer.prefetch_asset_records(
            [key for key in self.target_asset_keys if not self.asset_graph.is_source(key)]
        )
        self.instance_queryer.prefetch_asset_partition_counts(
            [
                key
                for key in self.target_asset_keys_and_parents
                if self.asset_graph.is_partitioned(key) and not self.asset_graph.is_source(key)
            ],
            after_cursor=cursor.latest_storage_id,
        )

    @property
    def instance_queryer(self) -> "CachingInstanceQueryer":
        return self._instance_queryer

    @property
    def cursor(self) -> AssetDaemonCursor:
        return self._cursor

    @property
    def asset_graph(self) -> AssetGraph:
        return self.instance_queryer.asset_graph

    @property
    def latest_storage_id(self) -> Optional[int]:
        return self.cursor.latest_storage_id

    @property
    def target_asset_keys(self) -> AbstractSet[AssetKey]:
        return self._target_asset_keys

    @property
    def target_asset_keys_and_parents(self) -> AbstractSet[AssetKey]:
        return {
            parent
            for asset_key in self.target_asset_keys
            for parent in self.asset_graph.get_parents(asset_key)
        } | self.target_asset_keys

    def get_implicit_auto_materialize_policy(
        self, asset_key: AssetKey
    ) -> Optional[AutoMaterializePolicy]:
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

    def find_never_handled_root_asset_partitions(
        self,
    ) -> Tuple[
        Iterable[AssetKeyPartitionKey],
        AbstractSet[AssetKey],
        Mapping[AssetKey, AbstractSet[str]],
    ]:
        """Finds asset partitions that have never been materialized or requested and that have no
        parents.

        Returns:
        - Asset (partition)s that have never been materialized or requested.
        - Non-partitioned assets that had never been materialized or requested up to the previous cursor
            but are now materialized.
        - Asset (partition)s that had never been materialized or requested up to the previous cursor but
            are now materialized.
        """
        never_handled = set()
        newly_materialized_root_asset_keys = set()
        newly_materialized_root_partitions_by_asset_key = defaultdict(set)

        for asset_key in self.target_asset_keys & self.asset_graph.root_asset_keys:
            if self.asset_graph.is_partitioned(asset_key):
                for partition_key in self.cursor.get_unhandled_partitions(
                    asset_key,
                    self.asset_graph,
                    dynamic_partitions_store=self.instance_queryer,
                    current_time=self.instance_queryer.evaluation_time,
                ):
                    asset_partition = AssetKeyPartitionKey(asset_key, partition_key)
                    if self.instance_queryer.asset_partition_has_materialization_or_observation(
                        asset_partition
                    ):
                        newly_materialized_root_partitions_by_asset_key[asset_key].add(
                            partition_key
                        )
                    else:
                        never_handled.add(asset_partition)
            else:
                if not self.cursor.was_previously_handled(asset_key):
                    asset_partition = AssetKeyPartitionKey(asset_key)
                    if self.instance_queryer.asset_partition_has_materialization_or_observation(
                        asset_partition
                    ):
                        newly_materialized_root_asset_keys.add(asset_key)
                    else:
                        never_handled.add(asset_partition)

        return (
            never_handled,
            newly_materialized_root_asset_keys,
            newly_materialized_root_partitions_by_asset_key,
        )

    def determine_asset_partitions_to_auto_materialize(
        self,
        conditions_by_asset_partition_for_freshness: Mapping[
            AssetKeyPartitionKey, Set[AutoMaterializeCondition]
        ],
    ) -> Tuple[
        Mapping[AssetKeyPartitionKey, AbstractSet[AutoMaterializeCondition]],
        AbstractSet[AssetKey],
        Mapping[AssetKey, AbstractSet[str]],
        Optional[int],
    ]:
        evaluation_time = self.instance_queryer.evaluation_time

        (
            never_handled_roots,
            newly_materialized_root_asset_keys,
            newly_materialized_root_partitions_by_asset_key,
        ) = self.find_never_handled_root_asset_partitions()

        # initialize conditions with the conditions_for_freshness
        conditions_by_asset_partition: Dict[
            AssetKeyPartitionKey, Set[AutoMaterializeCondition]
        ] = defaultdict(set, conditions_by_asset_partition_for_freshness)
        materialization_requests_by_asset_key: Dict[
            AssetKey, Set[AssetKeyPartitionKey]
        ] = defaultdict(set)

        def can_reconcile_candidate(candidate: AssetKeyPartitionKey) -> bool:
            """A filter for eliminating candidates from consideration for auto-materialization."""
            auto_materialize_policy = self.get_implicit_auto_materialize_policy(
                asset_key=candidate.asset_key
            )

            return not (
                # must have an auto_materialize_policy
                auto_materialize_policy is None
                # must be in the taget set
                or candidate.asset_key not in self.target_asset_keys
                # must not be currently backfilled
                or candidate
                in self.instance_queryer.get_active_backfill_target_asset_graph_subset()
                # must not have invalid parent partitions
                or len(
                    self.asset_graph.get_parents_partitions(
                        self.instance_queryer,
                        self.instance_queryer.evaluation_time,
                        candidate.asset_key,
                        candidate.partition_key,
                    ).required_but_nonexistent_parents_partitions
                )
                > 0
            )

        (
            stale_candidates,
            latest_storage_id,
        ) = self.instance_queryer.asset_partitions_with_newly_updated_parents_and_new_latest_storage_id(
            latest_storage_id=self.cursor.latest_storage_id,
            target_asset_keys=frozenset(self.target_asset_keys),
            target_asset_keys_and_parents=frozenset(self.target_asset_keys_and_parents),
            can_reconcile_fn=can_reconcile_candidate,
            map_old_time_partitions=False,
        )

        def get_waiting_on_asset_keys(candidate: AssetKeyPartitionKey) -> FrozenSet[AssetKey]:
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
                    AutoMaterializeDecisionType.from_conditions(
                        conditions_by_asset_partition.get(parent)
                    )
                    == AutoMaterializeDecisionType.MATERIALIZE
                    # the parent must have the same partitioning / partition key to be materialized
                    # alongside the candidate
                    and self.asset_graph.have_same_partitioning(
                        parent.asset_key, candidate.asset_key
                    )
                    and parent.partition_key == candidate.partition_key
                    # the parent must be in the same repository to be materialized alongside the candidate
                    and (
                        not isinstance(self.asset_graph, ExternalAssetGraph)
                        or self.asset_graph.get_repository_handle(candidate.asset_key)
                        == self.asset_graph.get_repository_handle(parent.asset_key)
                    )
                ):
                    unreconciled_ancestors.update(
                        self.instance_queryer.get_root_unreconciled_ancestors(
                            asset_partition=parent
                        )
                    )
            return frozenset(unreconciled_ancestors)

        def conditions_for_candidate(
            candidate: AssetKeyPartitionKey,
        ) -> AbstractSet[AutoMaterializeCondition]:
            """Returns a set of AutoMaterializeConditions that apply to a given candidate."""
            auto_materialize_policy = check.not_none(
                self.get_implicit_auto_materialize_policy(asset_key=candidate.asset_key)
            )
            conditions = set()

            # if this asset is missing
            if (
                auto_materialize_policy.on_missing
                and not self.instance_queryer.asset_partition_has_materialization_or_observation(
                    asset_partition=candidate
                )
            ):
                conditions.add(MissingAutoMaterializeCondition())

            # if parent data has been updated or will update
            elif auto_materialize_policy.on_new_parent_data:
                if not self.asset_graph.is_source(candidate.asset_key):
                    parent_asset_partitions = self.asset_graph.get_parents_partitions(
                        dynamic_partitions_store=self.instance_queryer,
                        current_time=evaluation_time,
                        asset_key=candidate.asset_key,
                        partition_key=candidate.partition_key,
                    ).parent_partitions

                    (
                        updated_parent_asset_partitions,
                        _,
                    ) = self.instance_queryer.get_updated_and_missing_parent_asset_partitions(
                        candidate, parent_asset_partitions
                    )
                    updated_parents = {
                        parent.asset_key for parent in updated_parent_asset_partitions
                    }

                    will_update_parents = set()
                    for parent in parent_asset_partitions:
                        if (
                            AutoMaterializeDecisionType.from_conditions(
                                conditions_by_asset_partition.get(parent)
                            )
                            == AutoMaterializeDecisionType.MATERIALIZE
                        ):
                            will_update_parents.add(parent.asset_key)

                    if updated_parents or will_update_parents:
                        conditions.add(
                            ParentMaterializedAutoMaterializeCondition(
                                updated_asset_keys=frozenset(updated_parents),
                                will_update_asset_keys=frozenset(will_update_parents),
                            )
                        )

            # if the parents will not be resolved this tick
            waiting_on_asset_keys = get_waiting_on_asset_keys(candidate)
            if waiting_on_asset_keys:
                conditions.add(
                    ParentOutdatedAutoMaterializeCondition(
                        waiting_on_asset_keys=waiting_on_asset_keys
                    )
                )

            if (
                # would be materialized
                AutoMaterializeDecisionType.from_conditions(conditions)
                == AutoMaterializeDecisionType.MATERIALIZE
                # has a rate limit
                and auto_materialize_policy.max_materializations_per_minute is not None
                # would exceed the rate limit
                and len(
                    materialization_requests_by_asset_key[candidate.asset_key].union({candidate})
                )
                > auto_materialize_policy.max_materializations_per_minute
            ):
                conditions.add(MaxMaterializationsExceededAutoMaterializeCondition())

            return conditions

        def should_reconcile(
            asset_graph: AssetGraph,
            candidates_unit: Iterable[AssetKeyPartitionKey],
            to_reconcile: AbstractSet[AssetKeyPartitionKey],
        ) -> bool:
            if any(not can_reconcile_candidate(candidate) for candidate in candidates_unit):
                return False
            # collect all conditions that apply to any candidate in the unit
            unit_conditions = set().union(
                *(conditions_for_candidate(candidate) for candidate in candidates_unit)
            )
            will_materialize = (
                AutoMaterializeDecisionType.from_conditions(unit_conditions)
                == AutoMaterializeDecisionType.MATERIALIZE
            )
            # for now, all candidates in the unit share the same conditions
            for candidate in candidates_unit:
                conditions_by_asset_partition[candidate].update(unit_conditions)
                if will_materialize:
                    materialization_requests_by_asset_key[candidate.asset_key].add(candidate)
            return will_materialize

        # will update conditions
        self.asset_graph.bfs_filter_asset_partitions(
            self.instance_queryer,
            lambda candidates_unit, to_reconcile: should_reconcile(
                self.asset_graph, candidates_unit, to_reconcile
            ),
            set(itertools.chain(never_handled_roots, stale_candidates)),
            evaluation_time,
        )

        return (
            conditions_by_asset_partition,
            newly_materialized_root_asset_keys,
            newly_materialized_root_partitions_by_asset_key,
            latest_storage_id,
        )

    def evaluate(
        self,
    ) -> Tuple[Sequence[RunRequest], AssetDaemonCursor, Sequence[AutoMaterializeAssetEvaluation],]:
        conditions_by_asset_partition_for_freshness = (
            determine_asset_partitions_to_auto_materialize_for_freshness(
                data_time_resolver=CachingDataTimeResolver(instance_queryer=self.instance_queryer),
                asset_graph=self.asset_graph,
                target_asset_keys=self.target_asset_keys,
                target_asset_keys_and_parents=self.target_asset_keys_and_parents,
                current_time=self.instance_queryer.evaluation_time,
            )
        )

        (
            conditions_by_asset_partition,
            newly_materialized_root_asset_keys,
            newly_materialized_root_partitions_by_asset_key,
            latest_storage_id,
        ) = self.determine_asset_partitions_to_auto_materialize(
            conditions_by_asset_partition_for_freshness=conditions_by_asset_partition_for_freshness,
        )

        observe_request_timestamp = pendulum.now().timestamp()
        auto_observe_run_requests = (
            get_auto_observe_run_requests(
                asset_graph=self.asset_graph,
                last_observe_request_timestamp_by_asset_key=self.cursor.last_observe_request_timestamp_by_asset_key,
                current_timestamp=observe_request_timestamp,
                run_tags=self._observe_run_tags,
            )
            if self._auto_observe
            else []
        )
        run_requests = [
            *build_run_requests(
                asset_partitions={
                    asset_partition
                    for asset_partition, conditions in conditions_by_asset_partition.items()
                    if AutoMaterializeDecisionType.from_conditions(conditions)
                    == AutoMaterializeDecisionType.MATERIALIZE
                },
                asset_graph=self.asset_graph,
                run_tags=self._materialize_run_tags,
            ),
            *auto_observe_run_requests,
        ]

        return (
            run_requests,
            self.cursor.with_updates(
                latest_storage_id=latest_storage_id,
                conditions_by_asset_partition=conditions_by_asset_partition,
                asset_graph=self.asset_graph,
                newly_materialized_root_asset_keys=newly_materialized_root_asset_keys,
                newly_materialized_root_partitions_by_asset_key=newly_materialized_root_partitions_by_asset_key,
                evaluation_id=self.cursor.evaluation_id + 1,
                newly_observe_requested_asset_keys=[
                    asset_key
                    for run_request in auto_observe_run_requests
                    for asset_key in cast(Sequence[AssetKey], run_request.asset_selection)
                ],
                observe_request_timestamp=observe_request_timestamp,
            ),
            build_auto_materialize_asset_evaluations(
                self.asset_graph,
                conditions_by_asset_partition,
                dynamic_partitions_store=self.instance_queryer,
            ),
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


def build_auto_materialize_asset_evaluations(
    asset_graph: AssetGraph,
    conditions_by_asset_partition: Mapping[
        AssetKeyPartitionKey, AbstractSet[AutoMaterializeCondition]
    ],
    dynamic_partitions_store: "DynamicPartitionsStore",
) -> Sequence[AutoMaterializeAssetEvaluation]:
    """Bundles up the conditions into AutoMaterializeAssetEvaluations."""
    conditions_by_asset_key: Dict[
        AssetKey, Dict[AssetKeyPartitionKey, AbstractSet[AutoMaterializeCondition]]
    ] = defaultdict(dict)

    # split into sub-dictionaries that hold only the conditions specific to each asset
    for asset_partition, conditions in conditions_by_asset_partition.items():
        conditions_by_asset_key[asset_partition.asset_key][asset_partition] = conditions

    return [
        AutoMaterializeAssetEvaluation.from_conditions(
            asset_graph, asset_key, conditions, dynamic_partitions_store
        )
        for asset_key, conditions in conditions_by_asset_key.items()
    ]


def get_auto_observe_run_requests(
    last_observe_request_timestamp_by_asset_key: Mapping[AssetKey, float],
    current_timestamp: float,
    asset_graph: AssetGraph,
    run_tags: Optional[Mapping[str, str]],
) -> Sequence[RunRequest]:
    assets_to_auto_observe: Set[AssetKey] = set()
    for asset_key in asset_graph.source_asset_keys:
        last_observe_request_timestamp = last_observe_request_timestamp_by_asset_key.get(asset_key)
        auto_observe_interval_minutes = asset_graph.get_auto_observe_interval_minutes(asset_key)

        if auto_observe_interval_minutes and (
            last_observe_request_timestamp is None
            or (
                last_observe_request_timestamp + auto_observe_interval_minutes * 60
                < current_timestamp
            )
        ):
            assets_to_auto_observe.add(asset_key)

    return [
        RunRequest(asset_selection=list(asset_keys), tags=run_tags)
        for asset_keys in asset_graph.split_asset_keys_by_repository(assets_to_auto_observe)
        if len(asset_keys) > 0
    ]

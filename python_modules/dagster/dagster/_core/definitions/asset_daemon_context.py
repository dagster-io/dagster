import datetime
import itertools
from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Dict,
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
    freshness_conditions_for_asset_key,
)
from dagster._core.definitions.partition_mapping import IdentityPartitionMapping
from dagster._core.definitions.run_request import RunRequest
from dagster._core.definitions.time_window_partition_mapping import TimeWindowPartitionMapping
from dagster._core.definitions.time_window_partitions import (
    get_time_partitions_def,
)
from dagster._utils.cached_method import cached_method

from .asset_daemon_cursor import AssetDaemonCursor
from .asset_graph import AssetGraph, sort_key_for_asset_partition
from .auto_materialize_condition import (
    AutoMaterializeAssetEvaluation,
    AutoMaterializeCondition,
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
        from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

        self._instance_queryer = CachingInstanceQueryer(instance, asset_graph)
        self._data_time_resolver = CachingDataTimeResolver(self.instance_queryer)
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
            [
                key
                for key in self.target_asset_keys_and_parents
                if not self.asset_graph.is_source(key)
            ]
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
    def data_time_resolver(self) -> CachingDataTimeResolver:
        return self._data_time_resolver

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

    @cached_method
    def _get_never_handled_and_newly_handled_root_asset_partitions(
        self,
    ) -> Tuple[
        Mapping[AssetKey, AbstractSet[AssetKeyPartitionKey]],
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
        never_handled = defaultdict(set)
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
                        never_handled[asset_key].add(asset_partition)
            else:
                if not self.cursor.was_previously_handled(asset_key):
                    asset_partition = AssetKeyPartitionKey(asset_key)
                    if self.instance_queryer.asset_partition_has_materialization_or_observation(
                        asset_partition
                    ):
                        newly_materialized_root_asset_keys.add(asset_key)
                    else:
                        never_handled[asset_key].add(asset_partition)

        return (
            never_handled,
            newly_materialized_root_asset_keys,
            newly_materialized_root_partitions_by_asset_key,
        )

    def get_never_handled_root_asset_partitions_for_key(
        self, asset_key: AssetKey
    ) -> AbstractSet[AssetKeyPartitionKey]:
        """Returns the set of root asset partitions that have never been handled for a given asset
        key. If the input asset key is not a root asset, this will always be an empty set.
        """
        never_handled, _, _ = self._get_never_handled_and_newly_handled_root_asset_partitions()
        return never_handled.get(asset_key, set())

    def get_newly_updated_roots(
        self,
    ) -> Tuple[AbstractSet[AssetKey], Mapping[AssetKey, AbstractSet[str]]]:
        """Returns the set of unpartitioned root asset keys that have been updated since the last
        tick, and a mapping from partitioned root asset keys to the set of partition keys that have
        been materialized since the last tick.
        """
        (
            _,
            newly_handled_keys,
            newly_handled_partitions_by_key,
        ) = self._get_never_handled_and_newly_handled_root_asset_partitions()
        return newly_handled_keys, newly_handled_partitions_by_key

    @cached_method
    def _get_asset_partitions_with_newly_updated_parents_by_key_and_new_latest_storage_id(
        self,
    ) -> Tuple[Mapping[AssetKey, AbstractSet[AssetKeyPartitionKey]], Optional[int]]:
        """Returns a mapping from asset keys to the set of asset partitions that have newly updated
        parents, and the new latest storage ID.
        """
        (
            asset_partitions,
            new_latest_storage_id,
        ) = self.instance_queryer.asset_partitions_with_newly_updated_parents_and_new_latest_storage_id(
            latest_storage_id=self.latest_storage_id,
            target_asset_keys=frozenset(self.target_asset_keys),
            target_asset_keys_and_parents=frozenset(self.target_asset_keys_and_parents),
            map_old_time_partitions=False,
        )
        ret = defaultdict(set)
        for asset_partition in asset_partitions:
            ret[asset_partition.asset_key].add(asset_partition)
        return ret, new_latest_storage_id

    def get_new_latest_storage_id(self) -> Optional[int]:
        """Returns the latest storage of all target asset keys since the last tick."""
        (
            _,
            new_latest_storage_id,
        ) = self._get_asset_partitions_with_newly_updated_parents_by_key_and_new_latest_storage_id()
        return new_latest_storage_id

    def get_asset_partitions_with_newly_updated_parents_for_key(
        self, asset_key: AssetKey
    ) -> AbstractSet[AssetKeyPartitionKey]:
        """Returns the set of asset partitions whose parents have been updated since the last tick
        for a given asset key.
        """
        (
            updated_parent_mapping,
            _,
        ) = self._get_asset_partitions_with_newly_updated_parents_by_key_and_new_latest_storage_id()
        return updated_parent_mapping.get(asset_key, set())

    def materializable_in_same_run(self, child_key: AssetKey, parent_key: AssetKey) -> bool:
        """Returns whether a child asset can be materialized in the same run as a parent asset."""
        from dagster._core.definitions.external_asset_graph import ExternalAssetGraph

        return (
            # both assets must be materializable
            child_key in self.asset_graph.materializable_asset_keys
            and parent_key in self.asset_graph.materializable_asset_keys
            # the parent must have the same partitioning
            and self.asset_graph.have_same_partitioning(child_key, parent_key)
            # the parent must have a simple partition mapping to the child
            and (
                not self.asset_graph.is_partitioned(parent_key)
                or isinstance(
                    self.asset_graph.get_partition_mapping(child_key, parent_key),
                    (TimeWindowPartitionMapping, IdentityPartitionMapping),
                )
            )
            # the parent must be in the same repository to be materialized alongside the candidate
            and (
                not isinstance(self.asset_graph, ExternalAssetGraph)
                or self.asset_graph.get_repository_handle(child_key)
                == self.asset_graph.get_repository_handle(parent_key)
            )
        )

    def get_parent_materialized_conditions_for_key(
        self,
        asset_key: AssetKey,
        will_materialize_mapping: Mapping[AssetKey, AbstractSet[AssetKeyPartitionKey]],
    ) -> Mapping[ParentMaterializedAutoMaterializeCondition, AbstractSet[AssetKeyPartitionKey]]:
        """Returns a mapping from ParentMaterializedAutoMaterializeCondition to the set of asset
        partitions that the condition applies to.
        """
        conditions = defaultdict(set)
        has_parents_that_will_update = set()

        # first, get the set of parents that will be materialized this tick, and see if we
        # can materialize this asset with those parents
        will_update_parents_by_asset_partition = defaultdict(set)
        for parent_key in self.asset_graph.get_parents(asset_key):
            if not self.materializable_in_same_run(asset_key, parent_key):
                continue
            for parent_partition in will_materialize_mapping.get(parent_key, set()):
                asset_partition = AssetKeyPartitionKey(asset_key, parent_partition.partition_key)
                will_update_parents_by_asset_partition[asset_partition].add(parent_key)
                has_parents_that_will_update.add(asset_partition)

        # next, for each asset partition of this asset which has newly-updated parents, or
        # has a parent that will update, create a ParentMaterializedAutoMaterializeCondition
        has_or_will_update = (
            self.get_asset_partitions_with_newly_updated_parents_for_key(asset_key)
            | has_parents_that_will_update
        )
        for asset_partition in has_or_will_update:
            parent_asset_partitions = self.asset_graph.get_parents_partitions(
                dynamic_partitions_store=self.instance_queryer,
                current_time=self.instance_queryer.evaluation_time,
                asset_key=asset_partition.asset_key,
                partition_key=asset_partition.partition_key,
            ).parent_partitions

            (
                updated_parent_asset_partitions,
                _,
            ) = self.instance_queryer.get_updated_and_missing_parent_asset_partitions(
                asset_partition,
                parent_asset_partitions,
            )
            updated_parents = {parent.asset_key for parent in updated_parent_asset_partitions}
            will_update_parents = will_update_parents_by_asset_partition[asset_partition]

            if updated_parents or will_update_parents:
                conditions[
                    ParentMaterializedAutoMaterializeCondition(
                        updated_asset_keys=frozenset(updated_parents),
                        will_update_asset_keys=frozenset(will_update_parents),
                    )
                ].add(asset_partition)
        return conditions

    def get_missing_conditions_for_key(
        self, asset_key: AssetKey, candidates: AbstractSet[AssetKeyPartitionKey]
    ) -> Mapping[MissingAutoMaterializeCondition, AbstractSet[AssetKeyPartitionKey]]:
        """Returns a mapping from MissingAutoMaterializeCondition to the set of asset
        partitions that the condition applies to.
        """
        missing_asset_partitions = self.get_never_handled_root_asset_partitions_for_key(asset_key)
        # in addition to missing root asset partitions, check any asset partitions that we plan to
        # materialize to see if they are missing
        for candidate in candidates | self.get_asset_partitions_with_newly_updated_parents_for_key(
            asset_key
        ):
            if not self.instance_queryer.asset_partition_has_materialization_or_observation(
                candidate
            ):
                missing_asset_partitions |= {candidate}
        return {MissingAutoMaterializeCondition(): missing_asset_partitions}

    def get_parent_outdated_conditions_for_key(
        self,
        asset_key: AssetKey,
        candidates: AbstractSet[AssetKeyPartitionKey],
        will_materialize_mapping: Mapping[AssetKey, AbstractSet[AssetKeyPartitionKey]],
    ) -> Mapping[ParentOutdatedAutoMaterializeCondition, AbstractSet[AssetKeyPartitionKey]]:
        conditions = defaultdict(set)
        for candidate in candidates:
            unreconciled_ancestors = set()
            # find the root cause of why this asset partition's parents are outdated (if any)
            for parent in self.asset_graph.get_parents_partitions(
                self.instance_queryer,
                self.instance_queryer.evaluation_time,
                asset_key,
                candidate.partition_key,
            ).parent_partitions:
                # parent will not be materialized this tick
                if parent not in will_materialize_mapping.get(
                    parent.asset_key, set()
                ) or not self.materializable_in_same_run(candidate.asset_key, parent.asset_key):
                    unreconciled_ancestors.update(
                        self.instance_queryer.get_root_unreconciled_ancestors(
                            asset_partition=parent
                        )
                    )
            if unreconciled_ancestors:
                conditions[
                    ParentOutdatedAutoMaterializeCondition(
                        waiting_on_asset_keys=frozenset(unreconciled_ancestors)
                    )
                ].update({candidate})
        return conditions

    def get_max_materializations_exceeded_conditions_for_key(
        self, asset_key: AssetKey, candidates: AbstractSet[AssetKeyPartitionKey], limit: int
    ) -> Mapping[
        MaxMaterializationsExceededAutoMaterializeCondition, AbstractSet[AssetKeyPartitionKey]
    ]:
        # the set of asset partitions which exceed the limit
        rate_limited_asset_partitions = set(
            sorted(candidates, key=lambda x: sort_key_for_asset_partition(self.asset_graph, x))[
                limit:
            ]
        )
        return {
            MaxMaterializationsExceededAutoMaterializeCondition(): rate_limited_asset_partitions
        }

    def get_auto_materialize_conditions_for_asset(
        self,
        asset_key: AssetKey,
        will_materialize_mapping: Mapping[AssetKey, AbstractSet[AssetKeyPartitionKey]],
        expected_data_time_mapping: Mapping[AssetKey, Optional[datetime.datetime]],
    ) -> Tuple[
        Mapping[AutoMaterializeCondition, AbstractSet[AssetKeyPartitionKey]],
        AbstractSet[AssetKeyPartitionKey],
        Optional[datetime.datetime],
    ]:
        """Evaluates the auto materialize policy of a given asset key.

        Params:
            - asset_key: The asset key to evaluate.
            - will_materialize_mapping: A mapping of AssetKey to the set of AssetKeyPartitionKeys
                that will be materialized this tick. As this function is called in topological order,
                this mapping will contain the expected materializations of all upstream assets.
            - expected_data_time_mapping: A mapping of AssetKey to the expected data time of the
                asset after this tick. As this function is called in topological order, this mapping
                will contain the expected data times of all upstream assets.

        Returns:
            - A mapping of AutoMaterializeCondition to the set of AssetKeyPartitionKeys that the
                condition applies to.
            - The set of AssetKeyPartitionKeys that should be materialized.
            - The expected data time of the asset after this tick.
        """
        auto_materialize_policy = check.not_none(
            self.get_implicit_auto_materialize_policy(asset_key)
        )

        # a mapping from AutoMaterializeCondition to the asset partitions that it applies to
        conditions: Dict[AutoMaterializeCondition, Set[AssetKeyPartitionKey]] = defaultdict(set)
        # a set of asset partitions that should be materialized
        candidates: Set[AssetKeyPartitionKey] = set()
        # the expected data time of the asset after this tick
        expected_data_time: Optional[datetime.datetime] = None

        # FreshnessAutoMaterializeCondition, DownstreamFreshnessAutoMaterializeCondition
        if auto_materialize_policy.for_freshness:
            (
                freshness_conditions,
                _,
                expected_data_time,
            ) = freshness_conditions_for_asset_key(
                asset_key=asset_key,
                data_time_resolver=self.data_time_resolver,
                asset_graph=self.asset_graph,
                current_time=self.instance_queryer.evaluation_time,
                will_materialize_mapping=will_materialize_mapping,
                expected_data_time_mapping=expected_data_time_mapping,
            )
            for condition, asset_partitions in freshness_conditions.items():
                conditions[condition].update(asset_partitions)
                candidates.update(asset_partitions)

        # ParentMaterializedAutoMaterializeCondition
        if auto_materialize_policy.on_new_parent_data:
            (parent_updated_conditions) = self.get_parent_materialized_conditions_for_key(
                asset_key, will_materialize_mapping
            )
            for condition, asset_partitions in parent_updated_conditions.items():
                conditions[condition].update(asset_partitions)
                candidates.update(asset_partitions)

        # MissingAutoMaterializeCondition
        if auto_materialize_policy.on_missing:
            missing_conditions = self.get_missing_conditions_for_key(asset_key, candidates)
            for condition, asset_partitions in missing_conditions.items():
                conditions[condition].update(asset_partitions)
                candidates.update(asset_partitions)

        # These should be conditions, but aren't currently, so we just manually strip out things
        # from our materialization set
        for candidate in list(candidates):
            if (
                # must not be part of an active asset backfill
                candidate in self.instance_queryer.get_active_backfill_target_asset_graph_subset()
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
            ):
                candidates.remove(candidate)
                for condition, asset_partitions in conditions.items():
                    if candidate in asset_partitions:
                        conditions[condition].remove(candidate)

        # ParentOutdatedAutoMaterializeCondition (currently no way to disable this)
        if True:
            parent_outdated_conditions = self.get_parent_outdated_conditions_for_key(
                asset_key, candidates, will_materialize_mapping
            )
            for condition, asset_partitions in parent_outdated_conditions.items():
                conditions[condition].update(asset_partitions)
                candidates.difference_update(asset_partitions)

        # MaxMaterializationsExceededAutoMaterializeCondition
        if auto_materialize_policy.max_materializations_per_minute is not None:
            for (
                condition,
                asset_partitions,
            ) in self.get_max_materializations_exceeded_conditions_for_key(
                asset_key, candidates, auto_materialize_policy.max_materializations_per_minute
            ).items():
                conditions[condition].update(asset_partitions)
                candidates.difference_update(asset_partitions)

        return conditions, candidates, expected_data_time

    def get_auto_materialize_conditions(
        self,
    ) -> Tuple[
        Mapping[AssetKey, Mapping[AutoMaterializeCondition, AbstractSet[AssetKeyPartitionKey]]],
        AbstractSet[AssetKeyPartitionKey],
    ]:
        """Returns a mapping from AutoMaterializeCondition to the set of asset partitions that it
        applies to for each asset key, as well as a set of all asset partitions that should be
        materialized this tick.
        """
        condition_mapping: Dict[
            AssetKey, Mapping[AutoMaterializeCondition, AbstractSet[AssetKeyPartitionKey]]
        ] = defaultdict()
        will_materialize_mapping: Dict[AssetKey, AbstractSet[AssetKeyPartitionKey]] = defaultdict(
            set
        )
        expected_data_time_mapping: Dict[AssetKey, Optional[datetime.datetime]] = defaultdict()
        visited_multi_asset_keys = set()
        for asset_key in itertools.chain(*self.asset_graph.toposort_asset_keys()):
            # an asset may have already been visited if it was part of a non-subsettable multi-asset
            if asset_key not in self.target_asset_keys or asset_key in visited_multi_asset_keys:
                continue
            (
                conditions_for_key,
                to_materialize,
                expected_data_time,
            ) = self.get_auto_materialize_conditions_for_asset(
                asset_key, will_materialize_mapping, expected_data_time_mapping
            )
            condition_mapping[asset_key] = conditions_for_key
            will_materialize_mapping[asset_key] = to_materialize
            expected_data_time_mapping[asset_key] = expected_data_time
            # if we need to materialize any partitions of a non-subsettable multi-asset, just copy
            # over conditions to any required neighbor key
            if to_materialize:
                for neighbor_key in self.asset_graph.get_required_multi_asset_keys(asset_key):
                    condition_mapping[neighbor_key] = {
                        condition: {ap._replace(asset_key=neighbor_key) for ap in asset_partitions}
                        for condition, asset_partitions in conditions_for_key.items()
                    }
                    will_materialize_mapping[neighbor_key] = {
                        ap._replace(asset_key=neighbor_key) for ap in to_materialize
                    }
                    expected_data_time_mapping[neighbor_key] = expected_data_time
                    visited_multi_asset_keys.add(neighbor_key)

        return condition_mapping, set().union(*will_materialize_mapping.values())

    def evaluate(
        self,
    ) -> Tuple[Sequence[RunRequest], AssetDaemonCursor, Sequence[AutoMaterializeAssetEvaluation],]:
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

        condition_mapping, to_materialize = self.get_auto_materialize_conditions()

        # here, we reorganize / flatten this into a mapping from asset partition to conditions
        conditions_by_asset_partition = defaultdict(set)
        for conditions_for_key in condition_mapping.values():
            for condition, asset_partitions in conditions_for_key.items():
                for asset_partition in asset_partitions:
                    conditions_by_asset_partition[asset_partition].add(condition)

        run_requests = [
            *build_run_requests(
                asset_partitions=to_materialize,
                asset_graph=self.asset_graph,
                run_tags=self._materialize_run_tags,
            ),
            *auto_observe_run_requests,
        ]

        (
            newly_materialized_root_asset_keys,
            newly_materialized_root_partitions_by_asset_key,
        ) = self.get_newly_updated_roots()

        return (
            run_requests,
            self.cursor.with_updates(
                latest_storage_id=self.get_new_latest_storage_id(),
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
                asset_graph=self.asset_graph,
                conditions_by_asset_partition=conditions_by_asset_partition,
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
        if conditions
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

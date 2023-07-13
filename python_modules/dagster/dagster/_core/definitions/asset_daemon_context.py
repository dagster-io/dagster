import datetime
import json
from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Dict,
    FrozenSet,
    Iterable,
    Mapping,
    NamedTuple,
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
from dagster._serdes.serdes import whitelist_for_serdes
from dagster._utils.cached_method import cached_method

from .asset_graph import AssetGraph
from .auto_materialize_condition import (
    AutoMaterializeCondition,
    AutoMaterializeDecisionType,
    MaxMaterializationsExceededAutoMaterializeCondition,
    MissingAutoMaterializeCondition,
    ParentMaterializedAutoMaterializeCondition,
    ParentOutdatedAutoMaterializeCondition,
)
from .partition import (
    PartitionsDefinition,
    PartitionsSubset,
    ScheduleType,
    SerializedPartitionsSubset,
)

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance, DynamicPartitionsStore
    from dagster._utils.caching_instance_queryer import CachingInstanceQueryer  # expensive import


def _decision_type_for_conditions(
    conditions: Optional[AbstractSet[AutoMaterializeCondition]],
) -> Optional[AutoMaterializeDecisionType]:
    """Based on a set of conditions, determine the resulting decision."""
    if not conditions:
        return None
    condition_decision_types = {condition.decision_type for condition in conditions}
    # precedence of decisions
    for decision_type in [
        AutoMaterializeDecisionType.SKIP,
        AutoMaterializeDecisionType.DISCARD,
        AutoMaterializeDecisionType.MATERIALIZE,
    ]:
        if decision_type in condition_decision_types:
            return decision_type
    return None


def _will_materialize_for_conditions(
    conditions: Optional[AbstractSet[AutoMaterializeCondition]],
) -> bool:
    """Based on a set of conditions, determine if the asset will be materialized."""
    return _decision_type_for_conditions(conditions) == AutoMaterializeDecisionType.MATERIALIZE


@whitelist_for_serdes
class AutoMaterializeAssetEvaluation(NamedTuple):
    """Represents the results of the auto-materialize logic for a single asset.

    Properties:
        asset_key (AssetKey): The asset key that was evaluated.
        partition_subsets_by_condition: The conditions that impact if the asset should be materialized, skipped, or
            discarded. If the asset is partitioned, this will be a list of tuples, where the first
            element is the condition and the second element is the serialized subset of partitions that the
            condition applies to. If it's not partitioned, the second element will be None.
    """

    asset_key: AssetKey
    partition_subsets_by_condition: Sequence[
        Tuple[AutoMaterializeCondition, Optional[SerializedPartitionsSubset]]
    ]
    num_requested: int
    num_skipped: int
    num_discarded: int
    run_ids: Set[str] = set()

    @staticmethod
    def from_conditions(
        asset_graph: AssetGraph,
        asset_key: AssetKey,
        conditions_by_asset_partition: Mapping[
            AssetKeyPartitionKey, AbstractSet[AutoMaterializeCondition]
        ],
        dynamic_partitions_store: "DynamicPartitionsStore",
    ) -> "AutoMaterializeAssetEvaluation":
        num_requested = 0
        num_skipped = 0
        num_discarded = 0

        for conditions in conditions_by_asset_partition.values():
            decision_type = _decision_type_for_conditions(conditions)
            if decision_type == AutoMaterializeDecisionType.MATERIALIZE:
                num_requested += 1
            elif decision_type == AutoMaterializeDecisionType.SKIP:
                num_skipped += 1
            elif decision_type == AutoMaterializeDecisionType.DISCARD:
                num_discarded += 1

        partitions_def = asset_graph.get_partitions_def(asset_key)
        if partitions_def is None:
            return AutoMaterializeAssetEvaluation(
                asset_key=asset_key,
                partition_subsets_by_condition=[
                    (condition, None)
                    for condition in set().union(*conditions_by_asset_partition.values())
                ],
                num_requested=num_requested,
                num_skipped=num_skipped,
                num_discarded=num_discarded,
            )
        else:
            partition_keys_by_condition = defaultdict(set)

            for asset_partition, conditions in conditions_by_asset_partition.items():
                for condition in conditions:
                    partition_keys_by_condition[condition].add(
                        check.not_none(asset_partition.partition_key)
                    )

            return AutoMaterializeAssetEvaluation(
                asset_key=asset_key,
                partition_subsets_by_condition=[
                    (
                        condition,
                        SerializedPartitionsSubset.from_subset(
                            subset=partitions_def.empty_subset().with_partition_keys(
                                partition_keys
                            ),
                            partitions_def=partitions_def,
                            dynamic_partitions_store=dynamic_partitions_store,
                        ),
                    )
                    for condition, partition_keys in partition_keys_by_condition.items()
                ],
                num_requested=num_requested,
                num_skipped=num_skipped,
                num_discarded=num_discarded,
            )


class AssetDaemonCursor(NamedTuple):
    """State that's saved between asset daemon evaluations.

    Attributes:
        latest_storage_id:
            The latest observed storage ID across all assets. Useful for finding out what has
            happened since the last tick.
        handled_root_asset_keys:
            Every entry is a non-partitioned asset with no parents that has been requested by this
            sensor, discarded by this sensor, or has been materialized (even if not by this sensor).
        handled_root_partitions_by_asset_key:
            Every key is a partitioned root asset. Every value is the set of that asset's partitions
            that have been requested by this sensor, discarded by this sensor,
            or have been materialized (even if not by this sensor).
        last_observe_request_timestamp_by_asset_key:
            Every key is an observable source asset that has been auto-observed. The value is the
            timestamp of the tick that requested the observation.
    """

    latest_storage_id: Optional[int]
    handled_root_asset_keys: AbstractSet[AssetKey]
    handled_root_partitions_by_asset_key: Mapping[AssetKey, PartitionsSubset]
    evaluation_id: int
    last_observe_request_timestamp_by_asset_key: Mapping[AssetKey, float]

    def get_unhandled_partitions(
        self,
        asset_key: AssetKey,
        asset_graph,
        dynamic_partitions_store: "DynamicPartitionsStore",
        current_time: datetime.datetime,
    ) -> Iterable[str]:
        partitions_def = asset_graph.get_partitions_def(asset_key)

        handled_subset = self.handled_root_partitions_by_asset_key.get(
            asset_key, partitions_def.empty_subset()
        )

        return handled_subset.get_partition_keys_not_in_subset(
            current_time=current_time,
            dynamic_partitions_store=dynamic_partitions_store,
        )

    def with_handled_asset_key(self, asset_key: AssetKey) -> "AssetDaemonCursor":
        return self._replace(handled_root_asset_keys=self.handled_root_asset_keys | {asset_key})

    def with_handled_asset_partitions(
        self,
        asset_graph: AssetGraph,
        asset_key: AssetKey,
        partition_keys: AbstractSet[str],
    ) -> "AssetDaemonCursor":
        prior_materialized_partitions = self.handled_root_partitions_by_asset_key.get(asset_key)
        if prior_materialized_partitions is None:
            prior_materialized_partitions = cast(
                PartitionsDefinition, asset_graph.get_partitions_def(asset_key)
            ).empty_subset()

        return self._replace(
            handled_root_partitions_by_asset_key={
                **self.handled_root_partitions_by_asset_key,
                **{asset_key: prior_materialized_partitions.with_partition_keys(partition_keys)},
            }
        )

    def with_conditions(
        self,
        asset_graph: AssetGraph,
        conditions_by_asset_partition_by_asset_key: Mapping[
            AssetKey, Mapping[AssetKeyPartitionKey, AbstractSet[AutoMaterializeCondition]]
        ],
    ) -> "AssetDaemonCursor":
        new_cursor = self
        for (
            asset_key,
            conditions_by_asset_partition,
        ) in conditions_by_asset_partition_by_asset_key.items():
            handled_partition_keys = {
                asset_partition.partition_key
                for asset_partition, conditions in conditions_by_asset_partition.items()
                if _decision_type_for_conditions(conditions)
                in (AutoMaterializeDecisionType.DISCARD, AutoMaterializeDecisionType.MATERIALIZE)
            }
            if not handled_partition_keys:
                continue
            elif asset_graph.is_partitioned(asset_key):
                new_cursor = new_cursor.with_handled_asset_partitions(
                    asset_graph, asset_key, {check.not_none(key) for key in handled_partition_keys}
                )
            else:
                new_cursor = new_cursor.with_handled_asset_key(asset_key)
        return new_cursor

    def with_observe_run_requests(
        self, observe_run_requests: Sequence[RunRequest], observe_request_timestamp: float
    ) -> "AssetDaemonCursor":
        result_last_observe_request_timestamp_by_asset_key = dict(
            self.last_observe_request_timestamp_by_asset_key
        )
        for asset_key in [
            asset_key
            for run_request in observe_run_requests
            for asset_key in cast(Sequence[AssetKey], run_request.asset_selection)
        ]:
            result_last_observe_request_timestamp_by_asset_key[
                asset_key
            ] = observe_request_timestamp
        return self._replace(
            last_observe_request_timestamp_by_asset_key=result_last_observe_request_timestamp_by_asset_key
        )

    @classmethod
    def empty(cls) -> "AssetDaemonCursor":
        return AssetDaemonCursor(
            latest_storage_id=None,
            handled_root_partitions_by_asset_key={},
            handled_root_asset_keys=set(),
            evaluation_id=0,
            last_observe_request_timestamp_by_asset_key={},
        )

    @classmethod
    def from_serialized(cls, cursor: str, asset_graph: AssetGraph) -> "AssetDaemonCursor":
        data = json.loads(cursor)

        if isinstance(data, list):  # backcompat
            check.invariant(len(data) in [3, 4], "Invalid serialized cursor")
            (
                latest_storage_id,
                serialized_handled_root_asset_keys,
                serialized_handled_root_partitions_by_asset_key,
            ) = data[:3]

            evaluation_id = data[3] if len(data) == 4 else 0
            serialized_last_observe_request_timestamp_by_asset_key = {}
        else:
            latest_storage_id = data["latest_storage_id"]
            serialized_handled_root_asset_keys = data["handled_root_asset_keys"]
            serialized_handled_root_partitions_by_asset_key = data[
                "handled_root_partitions_by_asset_key"
            ]
            evaluation_id = data["evaluation_id"]
            serialized_last_observe_request_timestamp_by_asset_key = data.get(
                "last_observe_request_timestamp_by_asset_key", {}
            )

        handled_root_partitions_by_asset_key = {}
        for (
            key_str,
            serialized_subset,
        ) in serialized_handled_root_partitions_by_asset_key.items():
            key = AssetKey.from_user_string(key_str)
            if key not in asset_graph.materializable_asset_keys:
                continue

            partitions_def = asset_graph.get_partitions_def(key)
            if partitions_def is None:
                continue

            try:
                # in the case that the partitions def has changed, we may not be able to deserialize
                # the corresponding subset. in this case, we just use an empty subset
                handled_root_partitions_by_asset_key[key] = partitions_def.deserialize_subset(
                    serialized_subset
                )
            except:
                handled_root_partitions_by_asset_key[key] = partitions_def.empty_subset()
        return cls(
            latest_storage_id=latest_storage_id,
            handled_root_asset_keys={
                AssetKey.from_user_string(key_str) for key_str in serialized_handled_root_asset_keys
            },
            handled_root_partitions_by_asset_key=handled_root_partitions_by_asset_key,
            evaluation_id=evaluation_id,
            last_observe_request_timestamp_by_asset_key={
                AssetKey.from_user_string(key_str): timestamp
                for key_str, timestamp in serialized_last_observe_request_timestamp_by_asset_key.items()
            },
        )

    @classmethod
    def get_evaluation_id_from_serialized(cls, cursor: str) -> Optional[int]:
        data = json.loads(cursor)
        if isinstance(data, list):  # backcompat
            check.invariant(len(data) in [3, 4], "Invalid serialized cursor")
            return data[3] if len(data) == 4 else None
        else:
            return data["evaluation_id"]

    def serialize(self) -> str:
        serializable_handled_root_partitions_by_asset_key = {
            key.to_user_string(): subset.serialize()
            for key, subset in self.handled_root_partitions_by_asset_key.items()
        }
        serialized = json.dumps(
            {
                "latest_storage_id": self.latest_storage_id,
                "handled_root_asset_keys": [
                    key.to_user_string() for key in self.handled_root_asset_keys
                ],
                "handled_root_partitions_by_asset_key": serializable_handled_root_partitions_by_asset_key,
                "evaluation_id": self.evaluation_id,
                "last_observe_request_timestamp_by_asset_key": {
                    key.to_user_string(): timestamp
                    for key, timestamp in self.last_observe_request_timestamp_by_asset_key.items()
                },
            }
        )
        return serialized


class AssetDaemonContext:
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

        self.new_cursor = stored_cursor._replace(evaluation_id=stored_cursor.evaluation_id + 1)

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

        self._conditions_by_asset_partition_by_asset_key: Dict[
            AssetKey, Dict[AssetKeyPartitionKey, AbstractSet[AutoMaterializeCondition]]
        ] = defaultdict(dict)
        self._will_materialize_asset_partitions: Dict[
            AssetKey, Set[AssetKeyPartitionKey]
        ] = defaultdict(set)

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

    def add_conditions(
        self,
        asset_partition: AssetKeyPartitionKey,
        conditions: AbstractSet[AutoMaterializeCondition],
    ):
        if conditions:
            self._conditions_by_asset_partition_by_asset_key[asset_partition.asset_key][
                asset_partition
            ] = (self.get_conditions(asset_partition) | conditions)

    def get_conditions(
        self, asset_partition: AssetKeyPartitionKey
    ) -> AbstractSet[AutoMaterializeCondition]:
        return self._conditions_by_asset_partition_by_asset_key[asset_partition.asset_key].get(
            asset_partition, set()
        )

    def will_materialize(self, asset_partition: AssetKeyPartitionKey) -> bool:
        return _will_materialize_for_conditions(self.get_conditions(asset_partition))

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
        self, candidate: AssetKeyPartitionKey
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
                self.will_materialize(parent)
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
        self, asset_partition: AssetKeyPartitionKey
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
        waiting_on_asset_keys = self.get_root_unreconciled_ancestors(asset_partition)
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
                self._will_materialize_asset_partitions[asset_partition.asset_key].union(
                    {asset_partition}
                )
            )
            > auto_materialize_policy.max_materializations_per_minute
        ):
            conditions.add(MaxMaterializationsExceededAutoMaterializeCondition())

        return conditions

    @cached_method
    def asset_partitions_with_newly_updated_parents(self) -> AbstractSet[AssetKeyPartitionKey]:
        (
            asset_partitions,
            latest_storage_id,
        ) = self.instance_queryer.asset_partitions_with_newly_updated_parents(
            after_cursor=self.stored_cursor.latest_storage_id,
            target_asset_keys=self.auto_materialize_asset_keys,
            target_asset_keys_and_parents=self.auto_materialize_asset_keys_and_parents,
        )
        self.new_cursor = self.new_cursor._replace(latest_storage_id=latest_storage_id)
        return asset_partitions

    def get_conditions_by_asset_partition(
        self,
    ) -> Mapping[AssetKey, Mapping[AssetKeyPartitionKey, AbstractSet[AutoMaterializeCondition]]]:
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
            self.add_conditions(asset_partition, conditions)

        def should_reconcile(
            asset_graph: AssetGraph,
            candidates_unit: Iterable[AssetKeyPartitionKey],
            to_reconcile: AbstractSet[AssetKeyPartitionKey],
        ) -> bool:
            if any(not self.can_materialize(candidate) for candidate in candidates_unit):
                return False
            # collect all conditions that apply to any candidate in the unit
            unit_conditions = set().union(
                *(self.conditions_for_candidate(candidate) for candidate in candidates_unit)
            )
            will_materialize = _will_materialize_for_conditions(unit_conditions)
            # for now, all candidates in the unit share the same conditions
            for candidate in candidates_unit:
                self.add_conditions(candidate, unit_conditions)
                if will_materialize:
                    self._will_materialize_asset_partitions[candidate.asset_key].add(candidate)
            return will_materialize

        # will add conditions to the internal mapping
        self.asset_graph.bfs_filter_asset_partitions(
            self.instance_queryer,
            lambda candidates_unit, to_reconcile: should_reconcile(
                self.asset_graph, candidates_unit, to_reconcile
            ),
            {
                *self.asset_partitions_with_newly_updated_parents(),
                *self.unhandled_root_asset_partitions(),
            },
            self.instance_queryer.evaluation_time,
        )
        # filter out empty sets of conditions
        return {
            asset_key: conditions_by_asset_partition
            for asset_key, conditions_by_asset_partition in self._conditions_by_asset_partition_by_asset_key.items()
            if conditions_by_asset_partition
        }

    def unhandled_root_asset_partitions(self) -> AbstractSet[AssetKeyPartitionKey]:
        """Finds asset partitions that have never been materialized, requested, or discarded and
        that have no parents.
        """
        unhandled_asset_partitions = set()
        for asset_key in self.asset_graph.root_asset_keys & self.auto_materialize_asset_keys:
            if not self.asset_graph.is_partitioned(asset_key):
                if asset_key not in self.stored_cursor.handled_root_asset_keys:
                    asset_partition = AssetKeyPartitionKey(asset_key)
                    if self.instance_queryer.asset_partition_has_materialization_or_observation(
                        asset_partition
                    ):
                        self.new_cursor = self.new_cursor.with_handled_asset_key(asset_key)
                        continue
                    else:
                        unhandled_asset_partitions.add(asset_partition)
            else:
                newly_materialized_partition_keys = set()
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
                        newly_materialized_partition_keys.add(partition_key)
                    else:
                        unhandled_asset_partitions.add(asset_partition)
                self.new_cursor = self.new_cursor.with_handled_asset_partitions(
                    self.asset_graph, asset_key, newly_materialized_partition_keys
                )
        return unhandled_asset_partitions

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
        observe_run_requests = (
            get_auto_observe_run_requests(
                self.stored_cursor.last_observe_request_timestamp_by_asset_key,
                observe_request_timestamp,
                self.asset_graph,
                observe_run_tags,
            )
            if auto_observe
            else []
        )
        self.new_cursor = self.new_cursor.with_observe_run_requests(
            observe_run_requests, observe_request_timestamp
        )

        return (
            [*observe_run_requests, *materialize_run_requests],
            self.new_cursor.with_conditions(
                self.asset_graph, conditions_by_asset_partition_by_asset_key
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

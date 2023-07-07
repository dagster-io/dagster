import datetime
import itertools
import json
from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Callable,
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
from dagster._annotations import experimental
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.time_window_partitions import (
    TimeWindow,
    TimeWindowPartitionsDefinition,
    get_time_partition_key,
    get_time_partitions_def,
)
from dagster._serdes.serdes import whitelist_for_serdes
from dagster._utils.backcompat import deprecation_warning

from .asset_graph import AssetGraph
from .asset_selection import AssetSelection
from .auto_materialize_condition import (
    AutoMaterializeCondition,
    AutoMaterializeDecisionType,
    MaxMaterializationsExceededAutoMaterializeCondition,
    MissingAutoMaterializeCondition,
    ParentMaterializedAutoMaterializeCondition,
    ParentOutdatedAutoMaterializeCondition,
)
from .decorators.sensor_decorator import sensor
from .freshness_based_auto_materialize import (
    determine_asset_partitions_to_auto_materialize_for_freshness,
)
from .partition import PartitionsDefinition, PartitionsSubset, SerializedPartitionsSubset
from .run_request import RunRequest
from .sensor_definition import DefaultSensorStatus, SensorDefinition
from .utils import check_valid_name

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance, DynamicPartitionsStore
    from dagster._utils.caching_instance_queryer import CachingInstanceQueryer  # expensive import


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
            if not conditions:
                continue
            decision_types = {condition.decision_type for condition in conditions}
            if AutoMaterializeDecisionType.DISCARD in decision_types:
                num_discarded += 1
            elif AutoMaterializeDecisionType.SKIP in decision_types:
                num_skipped += 1
            else:
                check.invariant(AutoMaterializeDecisionType.MATERIALIZE in decision_types)
                num_requested += 1

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


def get_implicit_auto_materialize_policy(
    asset_graph: AssetGraph, asset_key: AssetKey
) -> Optional[AutoMaterializePolicy]:
    """For backcompat with pre-auto materialize policy graphs, assume a default scope of 1 day."""
    auto_materialize_policy = asset_graph.get_auto_materialize_policy(asset_key)
    if auto_materialize_policy is None:
        return AutoMaterializePolicy(
            on_missing=True,
            on_new_parent_data=not bool(
                asset_graph.get_downstream_freshness_policies(asset_key=asset_key)
            ),
            for_freshness=True,
            time_window_partition_scope_minutes=24 * 60,
            max_materializations_per_minute=None,
        )
    return auto_materialize_policy


def reconciliation_window_for_time_window_partitions(
    partitions_def: TimeWindowPartitionsDefinition,
    time_window_partition_scope: Optional[datetime.timedelta],
    current_time: datetime.datetime,
) -> Optional[TimeWindow]:
    latest_partition_window = partitions_def.get_last_partition_window(current_time=current_time)
    earliest_partition_window = partitions_def.get_first_partition_window(current_time=current_time)
    if latest_partition_window is None or earliest_partition_window is None:
        return None

    allowable_start_time = (
        max(
            earliest_partition_window.start,
            latest_partition_window.start
            - time_window_partition_scope
            + datetime.timedelta.resolution,
        )
        if time_window_partition_scope is not None
        else earliest_partition_window.start
    )
    return TimeWindow(allowable_start_time, latest_partition_window.end)


def can_reconcile_time_window_partition(
    partitions_def: Optional[PartitionsDefinition],
    partition_key: Optional[str],
    time_window_partition_scope: Optional[datetime.timedelta],
    current_time: datetime.datetime,
) -> bool:
    time_partitions_def = get_time_partitions_def(partitions_def)
    if partition_key is None or time_partitions_def is None or time_window_partition_scope is None:
        return True
    time_partition_key = get_time_partition_key(partitions_def, partition_key)
    reconciliation_window = reconciliation_window_for_time_window_partitions(
        partitions_def=time_partitions_def,
        time_window_partition_scope=time_window_partition_scope,
        current_time=current_time,
    )
    if reconciliation_window is None:
        return False
    key_window = time_partitions_def.time_window_for_partition_key(time_partition_key)
    return (
        key_window.start >= reconciliation_window.start
        and key_window.end <= reconciliation_window.end
    )


class AssetReconciliationCursor(NamedTuple):
    """Attributes:
    latest_storage_id: The latest observed storage ID across all assets. Useful for
        finding out what has happened since the last tick.
    materialized_or_requested_root_asset_keys: Every entry is a non-partitioned asset with no
        parents that has been requested by this sensor or has been materialized (even if not by
        this sensor).
    materialized_or_requested_root_partitions_by_asset_key: Every key is a partitioned root
        asset. Every value is the set of that asset's partitoins that have been requested by
        this sensor or have been materialized (even if not by this sensor).
    """

    latest_storage_id: Optional[int]
    materialized_or_requested_root_asset_keys: AbstractSet[AssetKey]
    materialized_or_requested_root_partitions_by_asset_key: Mapping[AssetKey, PartitionsSubset]
    evaluation_id: int

    def was_previously_materialized_or_requested(self, asset_key: AssetKey) -> bool:
        return asset_key in self.materialized_or_requested_root_asset_keys

    def get_never_requested_never_materialized_partitions(
        self,
        asset_key: AssetKey,
        asset_graph,
        dynamic_partitions_store: "DynamicPartitionsStore",
        current_time: datetime.datetime,
        time_window_partition_scope: Optional[datetime.timedelta],
    ) -> Iterable[str]:
        partitions_def = asset_graph.get_partitions_def(asset_key)

        materialized_or_requested_subset = (
            self.materialized_or_requested_root_partitions_by_asset_key.get(
                asset_key, partitions_def.empty_subset()
            )
        )

        if isinstance(partitions_def, TimeWindowPartitionsDefinition):
            # for performance, only iterate over keys within the allowable time window
            reconciliation_window = reconciliation_window_for_time_window_partitions(
                partitions_def=partitions_def,
                time_window_partition_scope=time_window_partition_scope,
                current_time=current_time,
            )
            if reconciliation_window is None:
                return []
            # for performance, only iterate over keys within the allowable time window
            return [
                partition_key
                for partition_key in partitions_def.get_partition_keys_in_time_window(
                    reconciliation_window
                )
                if partition_key not in materialized_or_requested_subset
            ]
        else:
            return materialized_or_requested_subset.get_partition_keys_not_in_subset(
                current_time=current_time,
                dynamic_partitions_store=dynamic_partitions_store,
            )

    def with_updates(
        self,
        latest_storage_id: Optional[int],
        run_requests: Sequence[RunRequest],
        newly_materialized_root_asset_keys: AbstractSet[AssetKey],
        newly_materialized_root_partitions_by_asset_key: Mapping[AssetKey, AbstractSet[str]],
        evaluation_id: int,
        asset_graph: AssetGraph,
    ) -> "AssetReconciliationCursor":
        """Returns a cursor that represents this cursor plus the updates that have happened within the
        tick.
        """
        requested_root_partitions_by_asset_key: Dict[AssetKey, Set[str]] = defaultdict(set)
        requested_non_partitioned_root_assets: Set[AssetKey] = set()

        for run_request in run_requests:
            for asset_key in cast(Iterable[AssetKey], run_request.asset_selection):
                if not asset_graph.has_non_source_parents(asset_key):
                    if run_request.partition_key:
                        requested_root_partitions_by_asset_key[asset_key].add(
                            run_request.partition_key
                        )
                    else:
                        requested_non_partitioned_root_assets.add(asset_key)

        result_materialized_or_requested_root_partitions_by_asset_key = {
            **self.materialized_or_requested_root_partitions_by_asset_key
        }
        for asset_key in set(newly_materialized_root_partitions_by_asset_key.keys()) | set(
            requested_root_partitions_by_asset_key.keys()
        ):
            prior_materialized_partitions = (
                self.materialized_or_requested_root_partitions_by_asset_key.get(asset_key)
            )
            if prior_materialized_partitions is None:
                prior_materialized_partitions = cast(
                    PartitionsDefinition, asset_graph.get_partitions_def(asset_key)
                ).empty_subset()

            result_materialized_or_requested_root_partitions_by_asset_key[
                asset_key
            ] = prior_materialized_partitions.with_partition_keys(
                itertools.chain(
                    newly_materialized_root_partitions_by_asset_key[asset_key],
                    requested_root_partitions_by_asset_key[asset_key],
                )
            )

        result_materialized_or_requested_root_asset_keys = (
            self.materialized_or_requested_root_asset_keys
            | newly_materialized_root_asset_keys
            | requested_non_partitioned_root_assets
        )

        if latest_storage_id and self.latest_storage_id:
            check.invariant(
                latest_storage_id >= self.latest_storage_id,
                "Latest storage ID should be >= previous latest storage ID",
            )

        return AssetReconciliationCursor(
            latest_storage_id=latest_storage_id or self.latest_storage_id,
            materialized_or_requested_root_asset_keys=result_materialized_or_requested_root_asset_keys,
            materialized_or_requested_root_partitions_by_asset_key=result_materialized_or_requested_root_partitions_by_asset_key,
            evaluation_id=evaluation_id,
        )

    @classmethod
    def empty(cls) -> "AssetReconciliationCursor":
        return AssetReconciliationCursor(
            latest_storage_id=None,
            materialized_or_requested_root_partitions_by_asset_key={},
            materialized_or_requested_root_asset_keys=set(),
            evaluation_id=0,
        )

    @classmethod
    def from_serialized(cls, cursor: str, asset_graph: AssetGraph) -> "AssetReconciliationCursor":
        data = json.loads(cursor)
        check.invariant(len(data) in [3, 4], "Invalid serialized cursor")

        (
            latest_storage_id,
            serialized_materialized_or_requested_root_asset_keys,
            serialized_materialized_or_requested_root_partitions_by_asset_key,
        ) = data[:3]

        evaluation_id = data[3] if len(data) == 4 else 0

        materialized_or_requested_root_partitions_by_asset_key = {}
        for (
            key_str,
            serialized_subset,
        ) in serialized_materialized_or_requested_root_partitions_by_asset_key.items():
            key = AssetKey.from_user_string(key_str)
            if key not in asset_graph.non_source_asset_keys:
                continue

            partitions_def = asset_graph.get_partitions_def(key)
            if partitions_def is None:
                continue

            try:
                # in the case that the partitions def has changed, we may not be able to deserialize
                # the corresponding subset. in this case, we just use an empty subset
                materialized_or_requested_root_partitions_by_asset_key[
                    key
                ] = partitions_def.deserialize_subset(serialized_subset)
            except:
                materialized_or_requested_root_partitions_by_asset_key[
                    key
                ] = partitions_def.empty_subset()
        return cls(
            latest_storage_id=latest_storage_id,
            materialized_or_requested_root_asset_keys={
                AssetKey.from_user_string(key_str)
                for key_str in serialized_materialized_or_requested_root_asset_keys
            },
            materialized_or_requested_root_partitions_by_asset_key=materialized_or_requested_root_partitions_by_asset_key,
            evaluation_id=evaluation_id,
        )

    @classmethod
    def get_evaluation_id_from_serialized(cls, cursor: str) -> Optional[int]:
        data = json.loads(cursor)
        check.invariant(len(data) in [3, 4], "Invalid serialized cursor")
        return data[3] if len(data) == 4 else None

    def serialize(self) -> str:
        serializable_materialized_or_requested_root_partitions_by_asset_key = {
            key.to_user_string(): subset.serialize()
            for key, subset in self.materialized_or_requested_root_partitions_by_asset_key.items()
        }
        serialized = json.dumps(
            (
                self.latest_storage_id,
                [key.to_user_string() for key in self.materialized_or_requested_root_asset_keys],
                serializable_materialized_or_requested_root_partitions_by_asset_key,
                self.evaluation_id,
            )
        )
        return serialized


def find_parent_materialized_asset_partitions(
    instance_queryer: "CachingInstanceQueryer",
    latest_storage_id: Optional[int],
    target_asset_keys: AbstractSet[AssetKey],
    target_asset_keys_and_parents: AbstractSet[AssetKey],
    asset_graph: AssetGraph,
    can_reconcile_fn: Callable[[AssetKeyPartitionKey], bool] = lambda _: True,
) -> Tuple[AbstractSet[AssetKeyPartitionKey], Optional[int]]:
    """Finds asset partitions in the given selection whose parents have been materialized since
    latest_storage_id.

    Returns:
        - A set of asset partitions.
        - The latest observed storage_id across all relevant assets. Can be used to avoid scanning
            the same events the next time this function is called.
    """
    result_asset_partitions: Set[AssetKeyPartitionKey] = set()
    result_latest_storage_id = latest_storage_id

    for asset_key in target_asset_keys_and_parents:
        if asset_graph.is_source(asset_key) and not asset_graph.is_observable(asset_key):
            continue

        # the set of asset partitions which have been updated since the latest storage id
        new_asset_partitions = instance_queryer.get_asset_partitions_updated_after_cursor(
            asset_key=asset_key,
            asset_partitions=None,
            after_cursor=latest_storage_id,
        )
        if not new_asset_partitions:
            continue

        partitions_def = asset_graph.get_partitions_def(asset_key)
        if partitions_def is None:
            latest_record = check.not_none(
                instance_queryer.get_latest_materialization_or_observation_record(
                    AssetKeyPartitionKey(asset_key)
                )
            )
            for child in asset_graph.get_children_partitions(
                dynamic_partitions_store=instance_queryer,
                current_time=instance_queryer.evaluation_time,
                asset_key=asset_key,
            ):
                if (
                    child.asset_key in target_asset_keys
                    and not instance_queryer.is_asset_planned_for_run(latest_record.run_id, child)
                ):
                    result_asset_partitions.add(child)
        else:
            partitions_subset = partitions_def.empty_subset().with_partition_keys(
                [
                    asset_partition.partition_key
                    for asset_partition in new_asset_partitions
                    if asset_partition.partition_key is not None
                    and partitions_def.has_partition_key(
                        asset_partition.partition_key,
                        dynamic_partitions_store=instance_queryer,
                        current_time=instance_queryer.evaluation_time,
                    )
                ]
            )
            for child in asset_graph.get_children(asset_key):
                child_partitions_def = asset_graph.get_partitions_def(child)
                if child not in target_asset_keys:
                    continue
                elif not child_partitions_def:
                    result_asset_partitions.add(AssetKeyPartitionKey(child, None))
                else:
                    # we are mapping from the partitions of the parent asset to the partitions of
                    # the child asset
                    partition_mapping = asset_graph.get_partition_mapping(child, asset_key)
                    child_partitions_subset = (
                        partition_mapping.get_downstream_partitions_for_partitions(
                            partitions_subset,
                            downstream_partitions_def=child_partitions_def,
                            dynamic_partitions_store=instance_queryer,
                            current_time=instance_queryer.evaluation_time,
                        )
                    )
                    for child_partition in child_partitions_subset.get_partition_keys():
                        # we need to see if the child is planned for the same run, but this is
                        # expensive, so we try to avoid doing so in as many situations as possible
                        child_asset_partition = AssetKeyPartitionKey(child, child_partition)
                        if not can_reconcile_fn(child_asset_partition):
                            continue
                        # cannot materialize in the same run if different partitions defs or
                        # different partition keys
                        elif (
                            child_partitions_def != partitions_def
                            or child_partition not in partitions_subset
                        ):
                            result_asset_partitions.add(child_asset_partition)
                        else:
                            latest_partition_record = check.not_none(
                                instance_queryer.get_latest_materialization_or_observation_record(
                                    AssetKeyPartitionKey(asset_key, child_partition),
                                    after_cursor=latest_storage_id,
                                )
                            )
                            if not instance_queryer.is_asset_planned_for_run(
                                latest_partition_record.run_id, child
                            ):
                                result_asset_partitions.add(child_asset_partition)

        asset_latest_storage_id = (
            instance_queryer.get_latest_materialization_or_observation_storage_id(
                AssetKeyPartitionKey(asset_key)
            )
        )
        if (
            result_latest_storage_id is None
            or (asset_latest_storage_id or 0) > result_latest_storage_id
        ):
            result_latest_storage_id = asset_latest_storage_id

    return (result_asset_partitions, result_latest_storage_id)


def find_never_materialized_or_requested_root_asset_partitions(
    instance_queryer: "CachingInstanceQueryer",
    cursor: AssetReconciliationCursor,
    target_asset_keys: AbstractSet[AssetKey],
    asset_graph: AssetGraph,
) -> Tuple[
    Iterable[AssetKeyPartitionKey], AbstractSet[AssetKey], Mapping[AssetKey, AbstractSet[str]]
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
    never_materialized_or_requested = set()
    newly_materialized_root_asset_keys = set()
    newly_materialized_root_partitions_by_asset_key = defaultdict(set)

    for asset_key in target_asset_keys & asset_graph.root_asset_keys:
        if asset_graph.is_partitioned(asset_key):
            auto_materialize_policy = check.not_none(
                get_implicit_auto_materialize_policy(asset_graph, asset_key)
            )
            for partition_key in cursor.get_never_requested_never_materialized_partitions(
                asset_key,
                asset_graph,
                dynamic_partitions_store=instance_queryer,
                current_time=instance_queryer.evaluation_time,
                time_window_partition_scope=auto_materialize_policy.time_window_partition_scope,
            ):
                asset_partition = AssetKeyPartitionKey(asset_key, partition_key)
                if instance_queryer.asset_partition_has_materialization_or_observation(
                    asset_partition
                ):
                    newly_materialized_root_partitions_by_asset_key[asset_key].add(partition_key)
                else:
                    never_materialized_or_requested.add(asset_partition)
        else:
            if not cursor.was_previously_materialized_or_requested(asset_key):
                asset_partition = AssetKeyPartitionKey(asset_key)
                if instance_queryer.asset_partition_has_materialization_or_observation(
                    asset_partition
                ):
                    newly_materialized_root_asset_keys.add(asset_key)
                else:
                    never_materialized_or_requested.add(asset_partition)

    return (
        never_materialized_or_requested,
        newly_materialized_root_asset_keys,
        newly_materialized_root_partitions_by_asset_key,
    )


def _will_materialize_for_conditions(
    conditions: Optional[AbstractSet[AutoMaterializeCondition]],
) -> bool:
    """Based on a set of conditions, determine if the asset will be materialized."""
    conditions = conditions or set()
    return len(conditions) > 0 and all(
        condition.decision_type == AutoMaterializeDecisionType.MATERIALIZE
        for condition in conditions
    )


def determine_asset_partitions_to_auto_materialize(
    instance_queryer: "CachingInstanceQueryer",
    cursor: AssetReconciliationCursor,
    target_asset_keys: AbstractSet[AssetKey],
    target_asset_keys_and_parents: AbstractSet[AssetKey],
    asset_graph: AssetGraph,
    current_time: datetime.datetime,
    conditions_by_asset_partition_for_freshness: Mapping[
        AssetKeyPartitionKey, Set[AutoMaterializeCondition]
    ],
) -> Tuple[
    Mapping[AssetKeyPartitionKey, AbstractSet[AutoMaterializeCondition]],
    AbstractSet[AssetKey],
    Mapping[AssetKey, AbstractSet[str]],
    Optional[int],
]:
    evaluation_time = instance_queryer.evaluation_time

    (
        never_materialized_or_requested_roots,
        newly_materialized_root_asset_keys,
        newly_materialized_root_partitions_by_asset_key,
    ) = find_never_materialized_or_requested_root_asset_partitions(
        instance_queryer=instance_queryer,
        cursor=cursor,
        target_asset_keys=target_asset_keys,
        asset_graph=asset_graph,
    )

    # initialize conditions with the conditions_for_freshness
    conditions_by_asset_partition: Dict[
        AssetKeyPartitionKey, Set[AutoMaterializeCondition]
    ] = defaultdict(set, conditions_by_asset_partition_for_freshness)
    materialization_requests_by_asset_key: Dict[AssetKey, Set[AssetKeyPartitionKey]] = defaultdict(
        set
    )

    def can_reconcile_candidate(candidate: AssetKeyPartitionKey) -> bool:
        """A filter for eliminating candidates from consideration for auto-materialization."""
        auto_materialize_policy = get_implicit_auto_materialize_policy(
            asset_graph=asset_graph, asset_key=candidate.asset_key
        )

        return not (
            # must have an auto_materialize_policy
            auto_materialize_policy is None
            # must be in the taget set
            or candidate.asset_key not in target_asset_keys
            # must not be currently backfilled
            or candidate in instance_queryer.get_active_backfill_target_asset_graph_subset()
            # must not be too old
            or not can_reconcile_time_window_partition(
                partitions_def=asset_graph.get_partitions_def(candidate.asset_key),
                partition_key=candidate.partition_key,
                time_window_partition_scope=auto_materialize_policy.time_window_partition_scope,
                current_time=instance_queryer.evaluation_time,
            )
            # must not have invalid parent partitions
            or len(
                asset_graph.get_parents_partitions(
                    instance_queryer,
                    instance_queryer.evaluation_time,
                    candidate.asset_key,
                    candidate.partition_key,
                ).required_but_nonexistent_parents_partitions
            )
            > 0
        )

    stale_candidates, latest_storage_id = find_parent_materialized_asset_partitions(
        instance_queryer=instance_queryer,
        latest_storage_id=cursor.latest_storage_id,
        target_asset_keys=target_asset_keys,
        target_asset_keys_and_parents=target_asset_keys_and_parents,
        asset_graph=asset_graph,
        can_reconcile_fn=can_reconcile_candidate,
    )

    def get_waiting_on_asset_keys(candidate: AssetKeyPartitionKey) -> FrozenSet[AssetKey]:
        """Returns the set of ancestor asset keys that must be materialized before this asset can be
        materialized.
        """
        from dagster._core.definitions.external_asset_graph import ExternalAssetGraph

        unreconciled_ancestors = set()
        for parent in asset_graph.get_parents_partitions(
            instance_queryer,
            instance_queryer.evaluation_time,
            candidate.asset_key,
            candidate.partition_key,
        ).parent_partitions:
            # parent will not be materialized this tick
            if not (
                _will_materialize_for_conditions(conditions_by_asset_partition.get(parent))
                # the parent must have the same partitioning / partition key to be materialized
                # alongside the candidate
                and asset_graph.have_same_partitioning(parent.asset_key, candidate.asset_key)
                and parent.partition_key == candidate.partition_key
                # the parent must be in the same repository to be materialized alongside the candidate
                and (
                    not isinstance(asset_graph, ExternalAssetGraph)
                    or asset_graph.get_repository_handle(candidate.asset_key)
                    == asset_graph.get_repository_handle(parent.asset_key)
                )
            ):
                unreconciled_ancestors.update(
                    instance_queryer.get_root_unreconciled_ancestors(asset_partition=parent)
                )
        return frozenset(unreconciled_ancestors)

    def conditions_for_candidate(
        candidate: AssetKeyPartitionKey,
    ) -> AbstractSet[AutoMaterializeCondition]:
        """Returns a set of AutoMaterializeConditions that apply to a given candidate."""
        auto_materialize_policy = check.not_none(
            get_implicit_auto_materialize_policy(
                asset_graph=asset_graph, asset_key=candidate.asset_key
            )
        )
        conditions = set()

        # if this asset is missing
        if (
            auto_materialize_policy.on_missing
            and not instance_queryer.asset_partition_has_materialization_or_observation(
                asset_partition=candidate
            )
        ):
            conditions.add(MissingAutoMaterializeCondition())

        # if the parent has been updated
        if auto_materialize_policy.on_new_parent_data and not instance_queryer.is_reconciled(
            asset_partition=candidate
        ):
            conditions.add(ParentMaterializedAutoMaterializeCondition())

        # if the parents will not be resolved this tick
        waiting_on_asset_keys = get_waiting_on_asset_keys(candidate)
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
            and len(materialization_requests_by_asset_key[candidate.asset_key].union({candidate}))
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
        will_materialize = _will_materialize_for_conditions(unit_conditions)
        # for now, all candidates in the unit share the same conditions
        for candidate in candidates_unit:
            conditions_by_asset_partition[candidate].update(unit_conditions)
            if will_materialize:
                materialization_requests_by_asset_key[candidate.asset_key].add(candidate)
        return will_materialize

    # will update conditions
    asset_graph.bfs_filter_asset_partitions(
        instance_queryer,
        lambda candidates_unit, to_reconcile: should_reconcile(
            asset_graph, candidates_unit, to_reconcile
        ),
        set(itertools.chain(never_materialized_or_requested_roots, stale_candidates)),
        evaluation_time,
    )

    return (
        conditions_by_asset_partition,
        newly_materialized_root_asset_keys,
        newly_materialized_root_partitions_by_asset_key,
        latest_storage_id,
    )


def reconcile(
    asset_graph: AssetGraph,
    target_asset_keys: AbstractSet[AssetKey],
    instance: "DagsterInstance",
    cursor: AssetReconciliationCursor,
    run_tags: Optional[Mapping[str, str]],
) -> Tuple[
    Sequence[RunRequest],
    AssetReconciliationCursor,
    Sequence[AutoMaterializeAssetEvaluation],
]:
    from dagster._utils.caching_instance_queryer import CachingInstanceQueryer  # expensive import

    current_time = pendulum.now("UTC")

    instance_queryer = CachingInstanceQueryer(
        instance=instance, asset_graph=asset_graph, evaluation_time=current_time
    )

    target_parent_asset_keys = {
        parent
        for target_asset_key in target_asset_keys
        for parent in asset_graph.get_parents(target_asset_key)
    }
    target_asset_keys_and_parents = target_asset_keys | target_parent_asset_keys

    # fetch some data in advance to batch some queries
    target_asset_keys_and_parents_list = list(target_asset_keys_and_parents)
    instance_queryer.prefetch_asset_records(
        [key for key in target_asset_keys_and_parents_list if not asset_graph.is_source(key)]
    )
    instance_queryer.prefetch_asset_partition_counts(
        [
            key
            for key in target_asset_keys_and_parents_list
            if asset_graph.is_partitioned(key) and not asset_graph.is_source(key)
        ],
        after_cursor=cursor.latest_storage_id,
    )

    conditions_by_asset_partition_for_freshness = (
        determine_asset_partitions_to_auto_materialize_for_freshness(
            data_time_resolver=CachingDataTimeResolver(instance_queryer=instance_queryer),
            asset_graph=asset_graph,
            target_asset_keys=target_asset_keys,
            target_asset_keys_and_parents=target_asset_keys_and_parents,
            current_time=current_time,
        )
    )

    (
        conditions_by_asset_partition,
        newly_materialized_root_asset_keys,
        newly_materialized_root_partitions_by_asset_key,
        latest_storage_id,
    ) = determine_asset_partitions_to_auto_materialize(
        instance_queryer=instance_queryer,
        asset_graph=asset_graph,
        cursor=cursor,
        target_asset_keys=target_asset_keys,
        target_asset_keys_and_parents=target_asset_keys_and_parents,
        current_time=current_time,
        conditions_by_asset_partition_for_freshness=conditions_by_asset_partition_for_freshness,
    )

    run_requests = build_run_requests(
        asset_partitions={
            asset_partition
            for asset_partition, conditions in conditions_by_asset_partition.items()
            if _will_materialize_for_conditions(conditions)
        },
        asset_graph=asset_graph,
        run_tags=run_tags,
    )

    return (
        run_requests,
        cursor.with_updates(
            latest_storage_id=latest_storage_id,
            run_requests=run_requests,
            asset_graph=asset_graph,
            newly_materialized_root_asset_keys=newly_materialized_root_asset_keys,
            newly_materialized_root_partitions_by_asset_key=newly_materialized_root_partitions_by_asset_key,
            evaluation_id=cursor.evaluation_id + 1,
        ),
        build_auto_materialize_asset_evaluations(
            asset_graph, conditions_by_asset_partition, dynamic_partitions_store=instance_queryer
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


@experimental
def build_asset_reconciliation_sensor(
    asset_selection: AssetSelection,
    name: str = "asset_reconciliation_sensor",
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
    run_tags: Optional[Mapping[str, str]] = None,
) -> SensorDefinition:
    r"""Constructs a sensor that will monitor the provided assets and launch materializations to
    "reconcile" them.

    An asset is considered "unreconciled" if any of:

    - This sensor has never tried to materialize it and it has never been materialized.

    - Any of its parents have been materialized more recently than it has.

    - Any of its parents are unreconciled.

    - It is not currently up to date with respect to its freshness policy.

    The sensor won't try to reconcile any assets before their parents are reconciled. When multiple
    FreshnessPolicies require data from the same upstream assets, this sensor will attempt to
    launch a minimal number of runs of that asset to satisfy all constraints.

    Args:
        asset_selection (AssetSelection): The group of assets you want to keep up-to-date
        name (str): The name to give the sensor.
        minimum_interval_seconds (Optional[int]): The minimum amount of time that should elapse between sensor invocations.
        description (Optional[str]): A description for the sensor.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from the Dagster UI or via the GraphQL API.
        run_tags (Optional[Mapping[str, str]): Dictionary of tags to pass to the RunRequests launched by this sensor

    Returns:
        SensorDefinition

    Example:
        If you have the following asset graph, with no freshness policies:

        .. code-block:: python

            a       b       c
             \     / \     /
                d       e
                 \     /
                    f

        and create the sensor:

        .. code-block:: python

            build_asset_reconciliation_sensor(
                AssetSelection.assets(d, e, f),
                name="my_reconciliation_sensor",
            )

        You will observe the following behavior:
            * If ``a``, ``b``, and ``c`` are all materialized, then on the next sensor tick, the sensor will see that ``d`` and ``e`` can
              be materialized. Since ``d`` and ``e`` will be materialized, ``f`` can also be materialized. The sensor will kick off a
              run that will materialize ``d``, ``e``, and ``f``.
            * If, on the next sensor tick, none of ``a``, ``b``, and ``c`` have been materialized again, the sensor will not launch a run.
            * If, before the next sensor tick, just asset ``a`` and ``b`` have been materialized, the sensor will launch a run to
              materialize ``d``, ``e``, and ``f``, because they're downstream of ``a`` and ``b``.
              Even though ``c`` hasn't been materialized, the downstream assets can still be
              updated, because ``c`` is still considered "reconciled".

    Example:
        If you have the following asset graph, with the following freshness policies:
            * ``c: FreshnessPolicy(maximum_lag_minutes=120, cron_schedule="0 2 \* \* \*")``, meaning
              that by 2AM, c needs to be materialized with data from a and b that is no more than 120
              minutes old (i.e. all of yesterday's data).

        .. code-block:: python

            a     b
             \   /
               c

        and create the sensor:

        .. code-block:: python

            build_asset_reconciliation_sensor(
                AssetSelection.all(),
                name="my_reconciliation_sensor",
            )

        Assume that ``c`` currently has incorporated all source data up to ``2022-01-01 23:00``.

        You will observe the following behavior:
            * At any time between ``2022-01-02 00:00`` and ``2022-01-02 02:00``, the sensor will see that
              ``c`` will soon require data from ``2022-01-02 00:00``. In order to satisfy this
              requirement, there must be a materialization for both ``a`` and ``b`` with time >=
              ``2022-01-02 00:00``. If such a materialization does not exist for one of those assets,
              the missing asset(s) will be executed on this tick, to help satisfy the constraint imposed
              by ``c``. Materializing ``c`` in the same run as those assets will satisfy its
              required data constraint, and so the sensor will kick off a run for ``c`` alongside
              whichever upstream assets did not have up-to-date data.
            * On the next tick, the sensor will see that a run is currently planned which will
              satisfy that constraint, so no runs will be kicked off.
            * Once that run completes, a new materialization event will exist for ``c``, which will
              incorporate all of the required data, so no new runs will be kicked off until the
              following day.


    """
    check_valid_name(name)
    check.opt_mapping_param(run_tags, "run_tags", key_type=str, value_type=str)
    deprecation_warning(
        "build_asset_reconciliation_sensor", "1.4", "Use AutoMaterializePolicys instead."
    )

    @sensor(
        name=name,
        asset_selection=asset_selection,
        minimum_interval_seconds=minimum_interval_seconds,
        description=description,
        default_status=default_status,
    )
    def _sensor(context):
        asset_graph = context.repository_def.asset_graph
        cursor = (
            AssetReconciliationCursor.from_serialized(context.cursor, asset_graph)
            if context.cursor
            else AssetReconciliationCursor.empty()
        )

        # if there is a auto materialize policy set in the selection, filter down to that. Otherwise, use the
        # whole selection
        target_asset_keys = asset_selection.resolve(asset_graph)
        for target_key in target_asset_keys:
            check.invariant(
                asset_graph.get_auto_materialize_policy(target_key) is None,
                (
                    f"build_asset_reconciliation_sensor: Asset '{target_key.to_user_string()}' has"
                    " an AutoMaterializePolicy set. This asset will be automatically materialized"
                    " by the AssetDaemon, and should not be passed to this sensor. It's"
                    " recommended to remove this sensor once you have migrated to the"
                    " AutoMaterializePolicy api."
                ),
            )

        run_requests, updated_cursor, _ = reconcile(
            asset_graph=asset_graph,
            target_asset_keys=target_asset_keys,
            instance=context.instance,
            cursor=cursor,
            run_tags=run_tags,
        )

        context.update_cursor(updated_cursor.serialize())
        return run_requests

    return _sensor

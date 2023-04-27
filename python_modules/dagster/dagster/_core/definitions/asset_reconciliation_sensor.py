import datetime
import itertools
import json
from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Callable,
    Dict,
    Iterable,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
    cast,
)

import pendulum

import dagster._check as check
from dagster._annotations import experimental
from dagster._core.definitions.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionsDefinition
from dagster._core.definitions.time_window_partitions import (
    TimeWindow,
    TimeWindowPartitionsDefinition,
    has_one_dimension_time_window_partitioning,
)
from dagster._utils.backcompat import deprecation_warning
from dagster._utils.schedules import cron_string_iterator

from .asset_selection import AssetGraph, AssetSelection
from .decorators.sensor_decorator import sensor
from .partition import PartitionsDefinition, PartitionsSubset
from .run_request import RunRequest
from .sensor_definition import DefaultSensorStatus, SensorDefinition
from .utils import check_valid_name

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance, DynamicPartitionsStore
    from dagster._utils.caching_instance_queryer import CachingInstanceQueryer  # expensive import


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
        )
    return auto_materialize_policy


def reconciliation_window_for_time_window_partitions(
    partitions_def: Union[TimeWindowPartitionsDefinition, MultiPartitionsDefinition],
    time_window_partition_scope: Optional[datetime.timedelta],
    current_time: datetime.datetime,
) -> Optional[TimeWindow]:
    if isinstance(partitions_def, MultiPartitionsDefinition):
        time_partitions_def = cast(
            TimeWindowPartitionsDefinition, partitions_def.time_window_dimension.partitions_def
        )
    else:
        time_partitions_def = partitions_def

    latest_partition_window = time_partitions_def.get_last_partition_window(
        current_time=current_time
    )
    earliest_partition_window = time_partitions_def.get_first_partition_window(
        current_time=current_time
    )
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
    partitions_def: Union[TimeWindowPartitionsDefinition, MultiPartitionsDefinition],
    partition_key: Optional[str],
    time_window_partition_scope: Optional[datetime.timedelta],
    current_time: datetime.datetime,
) -> bool:
    if partition_key is None:
        return False
    if time_window_partition_scope is None:
        return True
    reconciliation_window = reconciliation_window_for_time_window_partitions(
        partitions_def=partitions_def,
        time_window_partition_scope=time_window_partition_scope,
        current_time=current_time,
    )
    if reconciliation_window is None:
        return False
    key_window = partitions_def.time_window_for_partition_key(partition_key)
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
                dynamic_partitions_store=dynamic_partitions_store
            )

    def with_updates(
        self,
        latest_storage_id: Optional[int],
        run_requests: Sequence[RunRequest],
        newly_materialized_root_asset_keys: AbstractSet[AssetKey],
        newly_materialized_root_partitions_by_asset_key: Mapping[AssetKey, AbstractSet[str]],
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
        )

    @classmethod
    def empty(cls) -> "AssetReconciliationCursor":
        return AssetReconciliationCursor(
            latest_storage_id=None,
            materialized_or_requested_root_partitions_by_asset_key={},
            materialized_or_requested_root_asset_keys=set(),
        )

    @classmethod
    def from_serialized(cls, cursor: str, asset_graph: AssetGraph) -> "AssetReconciliationCursor":
        (
            latest_storage_id,
            serialized_materialized_or_requested_root_asset_keys,
            serialized_materialized_or_requested_root_partitions_by_asset_key,
        ) = json.loads(cursor)
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
        )

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
            )
        )
        return serialized


def get_active_backfill_target_asset_graph_subset(
    instance: "DagsterInstance", asset_graph: AssetGraph
) -> AssetGraphSubset:
    """Returns an AssetGraphSubset representing the set of assets that are currently targeted by
    an active asset backfill.
    """
    from dagster._core.execution.asset_backfill import AssetBackfillData
    from dagster._core.execution.backfill import BulkActionStatus

    asset_backfills = [
        backfill
        for backfill in instance.get_backfills(status=BulkActionStatus.REQUESTED)
        if backfill.is_asset_backfill
    ]

    result = AssetGraphSubset(asset_graph)
    for asset_backfill in asset_backfills:
        if asset_backfill.serialized_asset_backfill_data is None:
            check.failed("Asset backfill missing serialized_asset_backfill_data")

        asset_backfill_data = AssetBackfillData.from_serialized(
            asset_backfill.serialized_asset_backfill_data, asset_graph
        )

        result |= asset_backfill_data.target_subset

    return result


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
        if asset_graph.is_source(asset_key):
            if asset_graph.is_observable(asset_key) and instance_queryer.new_version_exists(
                observable_source_asset_key=asset_key, after_cursor=latest_storage_id
            ):
                for child in asset_graph.get_children_partitions(
                    instance_queryer, asset_key, partition_key=None
                ):
                    if child.asset_key in target_asset_keys:
                        result_asset_partitions.add(child)

            continue

        partitions_def = asset_graph.get_partitions_def(asset_key)
        latest_record = instance_queryer.get_latest_materialization_record(
            asset_key, after_cursor=latest_storage_id
        )
        if latest_record is None:
            continue

        if partitions_def is None:
            for child in asset_graph.get_children_partitions(instance_queryer, asset_key):
                if (
                    child.asset_key in target_asset_keys
                    and not instance_queryer.is_asset_planned_for_run(latest_record.run_id, child)
                ):
                    result_asset_partitions.add(child)
        else:
            # for partitioned assets, we want the set of all asset partitions that have been
            # materialized since the latest_storage_id, not just the most recent
            materialized_partitions = [
                partition_key
                for partition_key in instance_queryer.get_materialized_partitions(
                    asset_key, after_cursor=latest_storage_id
                )
                if partitions_def.has_partition_key(
                    partition_key, dynamic_partitions_store=instance_queryer
                )
            ]

            partitions_subset = partitions_def.empty_subset().with_partition_keys(
                materialized_partitions
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
                            or child_partition not in materialized_partitions
                        ):
                            result_asset_partitions.add(child_asset_partition)
                        else:
                            latest_partition_record = check.not_none(
                                instance_queryer.get_latest_materialization_record(
                                    AssetKeyPartitionKey(asset_key, child_partition),
                                    after_cursor=latest_storage_id,
                                )
                            )
                            if not instance_queryer.is_asset_planned_for_run(
                                latest_partition_record.run_id, child
                            ):
                                result_asset_partitions.add(child_asset_partition)

        if result_latest_storage_id is None or latest_record.storage_id > result_latest_storage_id:
            result_latest_storage_id = latest_record.storage_id

    return (result_asset_partitions, result_latest_storage_id)


def find_never_materialized_or_requested_root_asset_partitions(
    instance_queryer: "CachingInstanceQueryer",
    cursor: AssetReconciliationCursor,
    target_asset_keys: AbstractSet[AssetKey],
    asset_graph: AssetGraph,
    current_time: datetime.datetime,
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
                instance_queryer,
                current_time,
                time_window_partition_scope=auto_materialize_policy.time_window_partition_scope,
            ):
                asset_partition = AssetKeyPartitionKey(asset_key, partition_key)
                if instance_queryer.get_latest_materialization_record(asset_partition, None):
                    newly_materialized_root_partitions_by_asset_key[asset_key].add(partition_key)
                else:
                    never_materialized_or_requested.add(asset_partition)
        else:
            if not cursor.was_previously_materialized_or_requested(asset_key):
                asset = AssetKeyPartitionKey(asset_key)
                if instance_queryer.get_latest_materialization_record(asset, None):
                    newly_materialized_root_asset_keys.add(asset_key)
                else:
                    never_materialized_or_requested.add(asset)

    return (
        never_materialized_or_requested,
        newly_materialized_root_asset_keys,
        newly_materialized_root_partitions_by_asset_key,
    )


def determine_asset_partitions_to_reconcile(
    instance_queryer: "CachingInstanceQueryer",
    cursor: AssetReconciliationCursor,
    target_asset_keys: AbstractSet[AssetKey],
    target_asset_keys_and_parents: AbstractSet[AssetKey],
    asset_graph: AssetGraph,
    current_time: datetime.datetime,
) -> Tuple[
    AbstractSet[AssetKeyPartitionKey],
    AbstractSet[AssetKey],
    Mapping[AssetKey, AbstractSet[str]],
    Optional[int],
]:
    (
        never_materialized_or_requested_roots,
        newly_materialized_root_asset_keys,
        newly_materialized_root_partitions_by_asset_key,
    ) = find_never_materialized_or_requested_root_asset_partitions(
        instance_queryer=instance_queryer,
        cursor=cursor,
        target_asset_keys=target_asset_keys,
        asset_graph=asset_graph,
        current_time=current_time,
    )

    # a filter for eliminating candidates
    def can_reconcile_candidate(candidate: AssetKeyPartitionKey) -> bool:
        auto_materialize_policy = get_implicit_auto_materialize_policy(
            asset_graph=asset_graph, asset_key=candidate.asset_key
        )
        partitions_def = asset_graph.get_partitions_def(candidate.asset_key)

        # no policy means no reconciliation
        if auto_materialize_policy is None:
            return False
        # the partition is too old to reconcile
        elif (
            partitions_def
            and has_one_dimension_time_window_partitioning(partitions_def)
            and not can_reconcile_time_window_partition(
                partitions_def=cast(
                    Union[TimeWindowPartitionsDefinition, MultiPartitionsDefinition], partitions_def
                ),
                partition_key=candidate.partition_key,
                time_window_partition_scope=auto_materialize_policy.time_window_partition_scope,
                current_time=current_time,
            )
        ):
            return False
        # the policy does not allow for materializing missing partitions and it's missing
        elif not auto_materialize_policy.on_missing and not instance_queryer.materialization_exists(
            candidate
        ):
            return False

        return True

    stale_candidates, latest_storage_id = find_parent_materialized_asset_partitions(
        instance_queryer=instance_queryer,
        latest_storage_id=cursor.latest_storage_id,
        target_asset_keys=target_asset_keys,
        target_asset_keys_and_parents=target_asset_keys_and_parents,
        asset_graph=asset_graph,
        can_reconcile_fn=can_reconcile_candidate,
    )

    backfill_target_asset_graph_subset = get_active_backfill_target_asset_graph_subset(
        asset_graph=asset_graph,
        instance=instance_queryer.instance,
    )

    def parents_will_be_reconciled(
        asset_graph: AssetGraph,
        candidate: AssetKeyPartitionKey,
        to_reconcile: AbstractSet[AssetKeyPartitionKey],
    ) -> bool:
        from dagster._core.definitions.external_asset_graph import ExternalAssetGraph

        for parent in asset_graph.get_parents_partitions(
            instance_queryer,
            candidate.asset_key,
            candidate.partition_key,
        ):
            if instance_queryer.is_reconciled(asset_partition=parent, asset_graph=asset_graph):
                continue

            if not (
                parent in to_reconcile
                # if they don't have the same partitioning, then we can't launch a run that
                # targets both, so we need to wait until the parent is reconciled before
                # launching a run for the child
                and asset_graph.have_same_partitioning(parent.asset_key, candidate.asset_key)
                and parent.partition_key == candidate.partition_key
            ):
                return False

            if isinstance(asset_graph, ExternalAssetGraph):
                # if the parent is in a different repository, we can't launch a run that targets both,
                # so we need to wait
                if asset_graph.get_repository_handle(
                    candidate.asset_key
                ) is not asset_graph.get_repository_handle(parent.asset_key):
                    return False

        return True

    def should_reconcile_candidate(candidate: AssetKeyPartitionKey) -> bool:
        auto_materialize_policy = get_implicit_auto_materialize_policy(
            asset_graph=asset_graph, asset_key=candidate.asset_key
        )
        if auto_materialize_policy is None:
            return False

        return (
            auto_materialize_policy.on_missing
            and not instance_queryer.materialization_exists(asset_partition=candidate)
        ) or (
            auto_materialize_policy.on_new_parent_data
            and not instance_queryer.is_reconciled(
                asset_partition=candidate, asset_graph=asset_graph
            )
        )

    def should_reconcile(
        asset_graph: AssetGraph,
        candidates_unit: Iterable[AssetKeyPartitionKey],
        to_reconcile: AbstractSet[AssetKeyPartitionKey],
    ) -> bool:
        if any(
            # do not reconcile assets if they are not reconcilable
            not can_reconcile_candidate(candidate)
            # do not reconcile assets if an active backfill will update them
            or candidate in backfill_target_asset_graph_subset
            # do not reconcile assets if they are not in the target selection
            or candidate.asset_key not in target_asset_keys
            for candidate in candidates_unit
        ):
            return False

        return all(
            parents_will_be_reconciled(asset_graph, candidate, to_reconcile)
            for candidate in candidates_unit
        ) and any(should_reconcile_candidate(candidate) for candidate in candidates_unit)

    to_reconcile = asset_graph.bfs_filter_asset_partitions(
        instance_queryer,
        lambda candidates_unit, to_reconcile: should_reconcile(
            asset_graph, candidates_unit, to_reconcile
        ),
        set(itertools.chain(never_materialized_or_requested_roots, stale_candidates)),
    )

    return (
        to_reconcile,
        newly_materialized_root_asset_keys,
        newly_materialized_root_partitions_by_asset_key,
        latest_storage_id,
    )


def get_execution_period_for_policy(
    freshness_policy: FreshnessPolicy,
    effective_data_time: Optional[datetime.datetime],
    current_time: datetime.datetime,
) -> pendulum.Period:
    if effective_data_time is None:
        return pendulum.Period(start=current_time, end=current_time)

    if freshness_policy.cron_schedule:
        tick_iterator = cron_string_iterator(
            start_timestamp=current_time.timestamp(),
            cron_string=freshness_policy.cron_schedule,
            execution_timezone=freshness_policy.cron_schedule_timezone,
        )

        while True:
            # find the next tick tick that requires data after the current effective data time
            # (usually, this will be the next tick)
            tick = next(tick_iterator)
            required_data_time = tick - freshness_policy.maximum_lag_delta
            if effective_data_time is None or effective_data_time < required_data_time:
                return pendulum.Period(start=required_data_time, end=tick)

    else:
        return pendulum.Period(
            # we don't want to execute this too frequently
            start=effective_data_time + 0.9 * freshness_policy.maximum_lag_delta,
            end=max(effective_data_time + freshness_policy.maximum_lag_delta, current_time),
        )


def get_execution_period_for_policies(
    policies: AbstractSet[FreshnessPolicy],
    effective_data_time: Optional[datetime.datetime],
    current_time: datetime.datetime,
) -> Optional[pendulum.Period]:
    """Determines a range of times for which you can kick off an execution of this asset to solve
    the most pressing constraint, alongside a maximum number of additional constraints.
    """
    merged_period = None
    for period in sorted(
        (
            get_execution_period_for_policy(policy, effective_data_time, current_time)
            for policy in policies
        ),
        # sort execution periods by most pressing
        key=lambda period: period.end,
    ):
        if merged_period is None:
            merged_period = period
        elif period.start <= merged_period.end:
            merged_period = pendulum.Period(
                start=max(period.start, merged_period.start),
                end=period.end,
            )
        else:
            break

    return merged_period


def determine_asset_partitions_to_reconcile_for_freshness(
    data_time_resolver: "CachingDataTimeResolver",
    asset_graph: AssetGraph,
    target_asset_keys: AbstractSet[AssetKey],
    target_asset_keys_and_parents: AbstractSet[AssetKey],
    current_time: datetime.datetime,
) -> AbstractSet[AssetKeyPartitionKey]:
    """Returns a set of AssetKeyPartitionKeys to materialize in order to abide by the given
    FreshnessPolicies, as well as a set of AssetKeyPartitionKeys which will be materialized at
    some point within the plan window.

    Attempts to minimize the total number of asset executions.
    """
    from dagster._core.definitions.external_asset_graph import ExternalAssetGraph

    # now we have a full set of constraints, we can find solutions for them as we move down
    to_materialize: Set[AssetKeyPartitionKey] = set()
    waiting_to_materialize: Set[AssetKey] = set()
    expected_data_time_by_key: Dict[AssetKey, Optional[datetime.datetime]] = {}

    for level in asset_graph.toposort_asset_keys():
        for key in level:
            if (
                key not in target_asset_keys_and_parents
                or key not in asset_graph.non_source_asset_keys
                or not asset_graph.get_downstream_freshness_policies(asset_key=key)
            ):
                continue

            parents = asset_graph.get_parents(key)

            if any(p in waiting_to_materialize for p in parents):
                # we can't materialize this asset yet, because we're waiting on a parent
                waiting_to_materialize.add(key)
                continue

            # if we're going to materialize a parent of this asset that's in a different repository,
            # then we need to wait
            if isinstance(asset_graph, ExternalAssetGraph):
                repo = asset_graph.get_repository_handle(key)
                if any(
                    AssetKeyPartitionKey(p, None) in to_materialize
                    and asset_graph.get_repository_handle(p) is not repo
                    for p in parents
                ):
                    waiting_to_materialize.add(key)
                    continue

            # figure out the current contents of this asset with respect to its constraints
            current_data_time = data_time_resolver.get_current_data_time(key, current_time)

            # figure out the expected data time of this asset if it were to be executed on this tick
            expected_data_time = min(
                (
                    cast(datetime.datetime, expected_data_time_by_key[k])
                    for k in parents
                    if k in expected_data_time_by_key and expected_data_time_by_key[k] is not None
                ),
                default=current_time,
            )

            if key in target_asset_keys:
                # calculate the data times you would expect after all currently-executing runs
                # were to successfully complete
                in_progress_data_time = data_time_resolver.get_in_progress_data_time(
                    key, current_time
                )

                # calculate the data times you would have expected if the most recent run succeeded
                failed_data_time = data_time_resolver.get_ignored_failure_data_time(
                    key, current_time
                )

                effective_data_time = max(
                    filter(None, (current_data_time, in_progress_data_time, failed_data_time)),
                    default=None,
                )

                # figure out a time period that you can execute this asset within to solve a maximum
                # number of constraints
                execution_period = get_execution_period_for_policies(
                    policies=asset_graph.get_downstream_freshness_policies(asset_key=key),
                    effective_data_time=effective_data_time,
                    current_time=current_time,
                )
            else:
                execution_period = None

            # a key may already be in to_materialize by the time we get here if a required
            # neighbor was selected to be updated
            asset_key_partition_key = AssetKeyPartitionKey(key, None)
            if asset_key_partition_key in to_materialize:
                expected_data_time_by_key[key] = expected_data_time
            elif (
                execution_period is not None
                and execution_period.start <= current_time
                and expected_data_time is not None
                and expected_data_time >= execution_period.start
            ):
                to_materialize.add(asset_key_partition_key)
                expected_data_time_by_key[key] = expected_data_time
                # all required neighbors will be updated on the same tick
                for required_key in asset_graph.get_required_multi_asset_keys(key):
                    to_materialize.add(AssetKeyPartitionKey(required_key, None))
            else:
                # if downstream assets consume this, they should expect data time equal to the
                # current time for this asset, as it's not going to be updated
                expected_data_time_by_key[key] = current_data_time

    return to_materialize


def reconcile(
    asset_graph: AssetGraph,
    target_asset_keys: AbstractSet[AssetKey],
    instance: "DagsterInstance",
    cursor: AssetReconciliationCursor,
    run_tags: Optional[Mapping[str, str]],
):
    from dagster._utils.caching_instance_queryer import CachingInstanceQueryer  # expensive import

    current_time = pendulum.now("UTC")

    instance_queryer = CachingInstanceQueryer(instance=instance)

    target_parent_asset_keys = {
        parent
        for target_asset_key in target_asset_keys
        for parent in asset_graph.get_parents(target_asset_key)
    }
    target_asset_keys_and_parents = target_asset_keys | target_parent_asset_keys

    # fetch some data in advance to batch some queries
    target_asset_keys_and_parents_list = list(target_asset_keys_and_parents)
    instance_queryer.prefetch_asset_records(target_asset_keys_and_parents_list)
    instance_queryer.prefetch_asset_partition_counts(
        target_asset_keys_and_parents_list, after_cursor=cursor.latest_storage_id
    )

    asset_partitions_to_reconcile_for_freshness = (
        determine_asset_partitions_to_reconcile_for_freshness(
            data_time_resolver=CachingDataTimeResolver(
                instance_queryer=instance_queryer, asset_graph=asset_graph
            ),
            asset_graph=asset_graph,
            target_asset_keys=target_asset_keys,
            target_asset_keys_and_parents=target_asset_keys_and_parents,
            current_time=current_time,
        )
    )

    (
        asset_partitions_to_reconcile,
        newly_materialized_root_asset_keys,
        newly_materialized_root_partitions_by_asset_key,
        latest_storage_id,
    ) = determine_asset_partitions_to_reconcile(
        instance_queryer=instance_queryer,
        asset_graph=asset_graph,
        cursor=cursor,
        target_asset_keys=target_asset_keys,
        target_asset_keys_and_parents=target_asset_keys_and_parents,
        current_time=current_time,
    )

    run_requests = build_run_requests(
        asset_partitions_to_reconcile | asset_partitions_to_reconcile_for_freshness,
        asset_graph,
        run_tags,
    )

    return run_requests, cursor.with_updates(
        latest_storage_id=latest_storage_id,
        run_requests=run_requests,
        asset_graph=asset_graph,
        newly_materialized_root_asset_keys=newly_materialized_root_asset_keys,
        newly_materialized_root_partitions_by_asset_key=newly_materialized_root_partitions_by_asset_key,
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
            status can be overridden from Dagit or via the GraphQL API.
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

        run_requests, updated_cursor = reconcile(
            asset_graph=asset_graph,
            target_asset_keys=target_asset_keys,
            instance=context.instance,
            cursor=cursor,
            run_tags=run_tags,
        )

        context.update_cursor(updated_cursor.serialize())
        return run_requests

    return _sensor

# pylint: disable=anomalous-backslash-in-string

import datetime
import itertools
import json
from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Dict,
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
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.freshness_policy import FreshnessConstraint
from dagster._core.definitions.time_window_partitions import (
    TimeWindow,
    TimeWindowPartitionsDefinition,
)
from dagster._core.storage.tags import PARTITION_NAME_TAG
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

from .asset_selection import AssetGraph, AssetSelection
from .decorators.sensor_decorator import sensor
from .partition import PartitionsDefinition, PartitionsSubset
from .repository_definition import RepositoryDefinition
from .run_request import RunRequest
from .sensor_definition import DefaultSensorStatus, SensorDefinition
from .utils import check_valid_name

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance


class AssetReconciliationCursor(NamedTuple):
    """
    Attributes:
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
        self, asset_key: AssetKey, asset_graph
    ) -> Iterable[str]:
        partitions_def = asset_graph.get_partitions_def(asset_key)

        materialized_or_requested_subset = (
            self.materialized_or_requested_root_partitions_by_asset_key.get(
                asset_key, partitions_def.empty_subset()
            )
        )

        if isinstance(partitions_def, TimeWindowPartitionsDefinition):
            allowable_time_window = allowable_time_window_for_partitions_def(partitions_def)
            if allowable_time_window is None:
                return []
            # for performance, only iterate over keys within the allowable time window
            return [
                partition_key
                for partition_key in partitions_def.get_partition_keys_in_time_window(
                    allowable_time_window
                )
                if partition_key not in materialized_or_requested_subset
            ]
        else:
            return materialized_or_requested_subset.get_partition_keys_not_in_subset()

    def with_updates(
        self,
        latest_storage_id: Optional[int],
        run_requests: Sequence[RunRequest],
        newly_materialized_root_asset_keys: AbstractSet[AssetKey],
        newly_materialized_root_partitions_by_asset_key: Mapping[AssetKey, AbstractSet[str]],
        asset_graph: AssetGraph,
    ) -> "AssetReconciliationCursor":
        """
        Returns a cursor that represents this cursor plus the updates that have happened within the
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
            materialized_or_requested_root_partitions_by_asset_key[key] = cast(
                PartitionsDefinition, asset_graph.get_partitions_def(key)
            ).deserialize_subset(serialized_subset)
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


def find_parent_materialized_asset_partitions(
    instance_queryer: CachingInstanceQueryer,
    latest_storage_id: Optional[int],
    target_asset_selection: AssetSelection,
    asset_graph: AssetGraph,
) -> Tuple[AbstractSet[AssetKeyPartitionKey], Optional[int]]:
    """
    Finds asset partitions in the given selection whose parents have been materialized since
    latest_storage_id.

    Returns:
        - A set of asset partitions.
        - The latest observed storage_id across all relevant assets. Can be used to avoid scanning
            the same events the next time this function is called.
    """
    result_asset_partitions: Set[AssetKeyPartitionKey] = set()
    result_latest_storage_id = latest_storage_id

    target_asset_keys = target_asset_selection.resolve(asset_graph)

    for asset_key in target_asset_selection.upstream(depth=1).resolve(asset_graph):
        records = instance_queryer.get_materialization_records(
            asset_key=asset_key, after_cursor=latest_storage_id
        )
        for record in records:
            for child in asset_graph.get_children_partitions(asset_key, record.partition_key):
                if child.asset_key in target_asset_keys and not instance_queryer.is_asset_in_run(
                    record.run_id, child
                ):
                    result_asset_partitions.add(child)

            if result_latest_storage_id is None or record.storage_id > result_latest_storage_id:
                result_latest_storage_id = record.storage_id

    return (result_asset_partitions, result_latest_storage_id)


def find_never_materialized_or_requested_root_asset_partitions(
    instance_queryer: CachingInstanceQueryer,
    cursor: AssetReconciliationCursor,
    target_asset_selection: AssetSelection,
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

    for asset_key in (target_asset_selection & AssetSelection.all().sources()).resolve(asset_graph):
        if asset_graph.is_partitioned(asset_key):
            for partition_key in cursor.get_never_requested_never_materialized_partitions(
                asset_key, asset_graph
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


def allowable_time_window_for_partitions_def(
    partitions_def: TimeWindowPartitionsDefinition,
) -> Optional[TimeWindow]:
    """Returns a time window encompassing the partitions that the reconciliation sensor is currently
    allowed to materialize for this partitions_def
    """
    latest_partition_window = partitions_def.get_last_partition_window()
    if latest_partition_window is None:
        return None
    return TimeWindow(
        start=latest_partition_window.start - datetime.timedelta(days=1),
        end=latest_partition_window.end,
    )


def candidates_unit_within_allowable_time_window(
    asset_graph: AssetGraph, candidates_unit: Iterable[AssetKeyPartitionKey]
):
    """A given time-window partition may only be materialized if its window ends within 1 day of the
    latest window for that partition.
    """
    representative_candidate = next(iter(candidates_unit), None)
    if not representative_candidate:
        return True

    partitions_def = asset_graph.get_partitions_def(representative_candidate.asset_key)
    partition_key = representative_candidate.partition_key
    if not isinstance(partitions_def, TimeWindowPartitionsDefinition) or not partition_key:
        return True

    partitions_def = cast(TimeWindowPartitionsDefinition, partitions_def)

    allowable_time_window = allowable_time_window_for_partitions_def(partitions_def)
    if allowable_time_window is None:
        return False

    candidate_partition_window = partitions_def.time_window_for_partition_key(partition_key)
    return (
        candidate_partition_window.start > allowable_time_window.start
        and candidate_partition_window.end <= allowable_time_window.end
    )


def determine_asset_partitions_to_reconcile(
    instance_queryer: CachingInstanceQueryer,
    cursor: AssetReconciliationCursor,
    target_asset_selection: AssetSelection,
    asset_graph: AssetGraph,
    eventual_asset_partitions_to_reconcile_for_freshness: AbstractSet[AssetKeyPartitionKey],
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
        target_asset_selection=target_asset_selection,
        asset_graph=asset_graph,
    )

    stale_candidates, latest_storage_id = find_parent_materialized_asset_partitions(
        instance_queryer=instance_queryer,
        latest_storage_id=cursor.latest_storage_id,
        target_asset_selection=target_asset_selection,
        asset_graph=asset_graph,
    )

    target_asset_keys = target_asset_selection.resolve(asset_graph)

    def parents_will_be_reconciled(
        candidate: AssetKeyPartitionKey,
        to_reconcile: AbstractSet[AssetKeyPartitionKey],
    ) -> bool:
        return all(
            (
                (
                    parent in to_reconcile
                    # if they don't have the same partitioning, then we can't launch a run that
                    # targets both, so we need to wait until the parent is reconciled before
                    # launching a run for the child
                    and asset_graph.have_same_partitioning(parent.asset_key, candidate.asset_key)
                    and parent.partition_key == candidate.partition_key
                )
                or (instance_queryer.is_reconciled(asset_partition=parent, asset_graph=asset_graph))
            )
            for parent in asset_graph.get_parents_partitions(
                candidate.asset_key, candidate.partition_key
            )
        )

    def should_reconcile(
        candidates_unit: Iterable[AssetKeyPartitionKey],
        to_reconcile: AbstractSet[AssetKeyPartitionKey],
    ) -> bool:
        if not candidates_unit_within_allowable_time_window(asset_graph, candidates_unit):
            return False

        if any(
            candidate in eventual_asset_partitions_to_reconcile_for_freshness
            or candidate.asset_key not in target_asset_keys
            for candidate in candidates_unit
        ):
            return False

        return all(
            parents_will_be_reconciled(candidate, to_reconcile) for candidate in candidates_unit
        ) and any(
            not instance_queryer.is_reconciled(asset_partition=candidate, asset_graph=asset_graph)
            for candidate in candidates_unit
        )

    to_reconcile = asset_graph.bfs_filter_asset_partitions(
        should_reconcile,
        set(itertools.chain(never_materialized_or_requested_roots, stale_candidates)),
    )

    return (
        to_reconcile,
        newly_materialized_root_asset_keys,
        newly_materialized_root_partitions_by_asset_key,
        latest_storage_id,
    )


def get_freshness_constraints_by_key(
    instance_queryer: CachingInstanceQueryer,
    asset_graph: AssetGraph,
    plan_window_start: datetime.datetime,
    plan_window_end: datetime.datetime,
) -> Mapping[AssetKey, AbstractSet[FreshnessConstraint]]:
    # a dictionary mapping each asset to a set of constraints that must be satisfied about the data
    # times of its upstream assets
    constraints_by_key: Dict[AssetKey, AbstractSet[FreshnessConstraint]] = defaultdict(set)

    # for each asset with a FreshnessPolicy, get all unsolved constraints for the given time window
    has_freshness_policy = False
    for key, freshness_policy in asset_graph.freshness_policies_by_key.items():
        if freshness_policy is None:
            continue
        has_freshness_policy = True
        upstream_keys = asset_graph.get_non_source_roots(key)
        constraints_by_key[key] = freshness_policy.constraints_for_time_window(
            window_start=plan_window_start,
            window_end=plan_window_end,
            upstream_keys=frozenset(upstream_keys),
        )

    # no freshness policies, so don't bother with constraints
    if not has_freshness_policy:
        return {}

    # propagate constraints upwards through the graph
    #
    # we ignore whether or not the constraint we're propagating corresponds to an asset which
    # is actually upstream of the asset we're operating on, as we'll filter those invalid
    # constraints out in the next step, and it's expensive to calculate if a given asset is
    # upstream of another asset.
    for level in reversed(asset_graph.toposort_asset_keys()):
        for key in level:
            if asset_graph.is_source(key):
                continue
            for upstream_key in asset_graph.get_parents(key):
                # pass along all of your constraints to your parents
                constraints_by_key[upstream_key] |= constraints_by_key[key]
    return constraints_by_key


def get_current_data_times_for_key(
    instance_queryer: CachingInstanceQueryer,
    asset_graph: AssetGraph,
    relevant_upstream_keys: AbstractSet[AssetKey],
    asset_key: AssetKey,
) -> Mapping[AssetKey, Optional[datetime.datetime]]:
    # calculate the data time for this record in relation to the upstream keys which are
    # set to be updated this tick and are involved in some constraint
    latest_record = instance_queryer.get_latest_materialization_record(asset_key)
    if latest_record is None:
        return {upstream_key: None for upstream_key in relevant_upstream_keys}
    else:
        return instance_queryer.get_used_data_times_for_record(
            asset_graph=asset_graph,
            record=latest_record,
        )


def get_expected_data_times_for_key(
    asset_graph: AssetGraph,
    current_time: datetime.datetime,
    expected_data_times_by_key: Mapping[AssetKey, Mapping[AssetKey, Optional[datetime.datetime]]],
    asset_key: AssetKey,
) -> Mapping[AssetKey, Optional[datetime.datetime]]:
    """Returns the data times for the given asset key if this asset were to be executed in this
    tick.
    """
    expected_data_times: Dict[AssetKey, Optional[datetime.datetime]] = {asset_key: current_time}

    def _min_or_none(a, b):
        if a is None or b is None:
            return None
        return min(a, b)

    # get the expected data time for each upstream asset key if you were to run this asset on
    # this tick
    for upstream_key in asset_graph.get_parents(asset_key):
        for upstream_upstream_key, expected_data_time in expected_data_times_by_key[
            upstream_key
        ].items():
            # take the minimum data time from each of your parents that uses this key
            expected_data_times[upstream_upstream_key] = _min_or_none(
                expected_data_times.get(upstream_upstream_key, expected_data_time),
                expected_data_time,
            )

    return expected_data_times


def get_execution_time_window_for_constraints(
    constraints: AbstractSet[FreshnessConstraint],
    current_data_times: Mapping[AssetKey, Optional[datetime.datetime]],
    in_progress_data_times: Mapping[AssetKey, Optional[datetime.datetime]],
    failed_data_times: Mapping[AssetKey, Optional[datetime.datetime]],
    expected_data_times: Mapping[AssetKey, Optional[datetime.datetime]],
    relevant_upstream_keys: AbstractSet[AssetKey],
) -> Tuple[Optional[datetime.datetime], Optional[datetime.datetime]]:
    """Determines a range of times for which you can kick off an execution of this asset to solve
    the most pressing constraint, alongside a maximum number of additional constraints.
    """
    currently_executable = False
    execution_window_start = None
    execution_window_end = None
    min_dt = datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)

    for constraint in sorted(constraints, key=lambda c: c.required_by_time):
        # the set of keys in this constraint that are actually upstream of this asset
        relevant_constraint_keys = constraint.asset_keys & relevant_upstream_keys

        if not all(
            # ensure that this constraint is not satisfied by the current state of the data and
            # will not be satisfied once all in progress runs complete, and was not intended to
            # be satisfied by a run that failed
            (current_data_times.get(key) or min_dt) >= constraint.required_data_time
            or (in_progress_data_times.get(key) or min_dt) >= constraint.required_data_time
            or (failed_data_times.get(key) or min_dt) >= constraint.required_data_time
            for key in relevant_constraint_keys
        ):
            # for this constraint, if all required data times will be satisfied by an execution
            # on this tick, it is valid to execute this asset
            if all(
                (expected_data_times.get(key) or min_dt) >= constraint.required_data_time
                for key in relevant_constraint_keys
            ):
                currently_executable = True

            # you can solve this constraint within the existing execution window
            if execution_window_end is None or constraint.required_data_time < execution_window_end:
                execution_window_start = max(
                    execution_window_start or constraint.required_data_time,
                    constraint.required_data_time,
                )
                execution_window_end = min(
                    execution_window_end or constraint.required_by_time,
                    constraint.required_by_time,
                )
            else:
                break

    if not currently_executable:
        return None, execution_window_end

    return execution_window_start, execution_window_end


def determine_asset_partitions_to_reconcile_for_freshness(
    instance_queryer: CachingInstanceQueryer,
    asset_graph: AssetGraph,
    target_asset_selection: AssetSelection,
) -> Tuple[AbstractSet[AssetKeyPartitionKey], AbstractSet[AssetKeyPartitionKey]]:
    """Returns a set of AssetKeyPartitionKeys to materialize in order to abide by the given
    FreshnessPolicies, as well as a set of AssetKeyPartitionKeys which will be materialized at
    some point within the plan window.

    Attempts to minimize the total number of asset executions.
    """
    # look within a 12-hour time window to combine future runs together
    current_time = pendulum.now(tz=pendulum.UTC)
    plan_window_start = current_time
    plan_window_end = plan_window_start + datetime.timedelta(hours=12)

    # get a set of constraints that must be satisfied for each key
    constraints_by_key = get_freshness_constraints_by_key(
        instance_queryer, asset_graph, plan_window_start, plan_window_end
    )

    # no constraints, so exit early
    if not constraints_by_key:
        return (set(), set())

    # get the set of asset keys we're allowed to execute
    target_asset_keys = target_asset_selection.resolve(asset_graph)

    # now we have a full set of constraints, we can find solutions for them as we move down
    to_materialize: Set[AssetKeyPartitionKey] = set()
    eventually_materialize: Set[AssetKeyPartitionKey] = set()
    expected_data_times_by_key: Dict[
        AssetKey, Mapping[AssetKey, Optional[datetime.datetime]]
    ] = defaultdict(dict)
    for level in asset_graph.toposort_asset_keys():
        for key in level:
            if asset_graph.is_source(key):
                continue
            # no need to evaluate this key, as it has no constraints
            constraints = constraints_by_key[key]
            if not constraints:
                continue

            constraint_keys = set().union(*(constraint.asset_keys for constraint in constraints))

            # the set of asset keys which are involved in some constraint and are actually upstream
            # of this asset
            relevant_upstream_keys = frozenset(
                set().union(
                    *(
                        expected_data_times_by_key[parent_key].keys()
                        for parent_key in asset_graph.get_parents(key)
                    )
                )
                & constraint_keys
            ) | {key}

            # figure out the current contents of this asset with respect to its constraints
            current_data_times = get_current_data_times_for_key(
                instance_queryer, asset_graph, relevant_upstream_keys, key
            )

            # should not execute if key is not targeted or previous run failed
            if key not in target_asset_keys:
                # cannot execute this asset, so if something consumes it, it should expect to
                # recieve the current contents of the asset
                execution_window_start = None
                expected_data_times: Mapping[AssetKey, Optional[datetime.datetime]] = {}
            else:
                # calculate the data times you would expect after all currently-executing runs
                # were to successfully complete
                in_progress_data_times = instance_queryer.get_in_progress_data_times_for_key(
                    asset_graph, key, current_time
                )

                # if the latest run for this asset failed, then calculate the data times you would
                # have expected after that failed run completed
                failed_data_times = instance_queryer.get_failed_data_times_for_key(
                    asset_graph, key, relevant_upstream_keys
                )
                # calculate the data times you'd expect for this key if you were to run it
                expected_data_times = get_expected_data_times_for_key(
                    asset_graph, current_time, expected_data_times_by_key, key
                )

                # figure out a time window that you can execute this asset within to solve a maximum
                # number of constraints
                (
                    execution_window_start,
                    execution_window_end,
                ) = get_execution_time_window_for_constraints(
                    constraints=constraints,
                    current_data_times=current_data_times,
                    in_progress_data_times=in_progress_data_times,
                    failed_data_times=failed_data_times,
                    expected_data_times=expected_data_times,
                    relevant_upstream_keys=relevant_upstream_keys,
                )

                # this key will be updated within the plan window
                if execution_window_end is not None and execution_window_end <= plan_window_end:
                    eventually_materialize.add(AssetKeyPartitionKey(key, None))

            # a key may already be in to_materialize by the time we get here if a required
            # neighbor was selected to be updated
            asset_key_partition_key = AssetKeyPartitionKey(key, None)
            if asset_key_partition_key in to_materialize:
                expected_data_times_by_key[key] = expected_data_times
            elif (
                # this key should be updated on this tick, as we are within the allowable window
                execution_window_start is not None
                and execution_window_start <= current_time
            ):
                to_materialize.add(asset_key_partition_key)
                expected_data_times_by_key[key] = expected_data_times
                # all required neighbors will be updated on the same tick
                for required_key in asset_graph.get_required_multi_asset_keys(key):
                    to_materialize.add(AssetKeyPartitionKey(required_key, None))
            else:
                # if downstream assets consume this, they should expect data times equal to the
                # current times for this asset, as it's not going to be updated
                expected_data_times_by_key[key] = current_data_times

    return to_materialize, eventually_materialize


def reconcile(
    repository_def: RepositoryDefinition,
    asset_selection: AssetSelection,
    instance: "DagsterInstance",
    cursor: AssetReconciliationCursor,
    run_tags: Optional[Mapping[str, str]],
):
    instance_queryer = CachingInstanceQueryer(instance=instance)
    asset_graph = repository_def.asset_graph

    (
        asset_partitions_to_reconcile_for_freshness,
        eventual_asset_partitions_to_reconcile_for_freshness,
    ) = determine_asset_partitions_to_reconcile_for_freshness(
        instance_queryer=instance_queryer,
        asset_graph=asset_graph,
        target_asset_selection=asset_selection,
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
        target_asset_selection=asset_selection,
        eventual_asset_partitions_to_reconcile_for_freshness=eventual_asset_partitions_to_reconcile_for_freshness,
    )

    run_requests = build_run_requests(
        asset_partitions_to_reconcile | asset_partitions_to_reconcile_for_freshness,
        asset_graph,
        run_tags,
    )

    return run_requests, cursor.with_updates(
        latest_storage_id=latest_storage_id,
        run_requests=run_requests,
        asset_graph=repository_def.asset_graph,
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
        _,
        partition_key,
    ), asset_keys in assets_to_reconcile_by_partitions_def_partition_key.items():
        tags = {**(run_tags or {})}
        if partition_key is not None:
            tags[PARTITION_NAME_TAG] = partition_key

        run_requests.append(
            RunRequest(
                asset_selection=list(asset_keys),
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

    @sensor(
        name=name,
        asset_selection=asset_selection,
        minimum_interval_seconds=minimum_interval_seconds,
        description=description,
        default_status=default_status,
    )
    def _sensor(context):
        cursor = (
            AssetReconciliationCursor.from_serialized(
                context.cursor, context.repository_def.asset_graph
            )
            if context.cursor
            else AssetReconciliationCursor.empty()
        )
        run_requests, updated_cursor = reconcile(
            repository_def=context.repository_def,
            asset_selection=asset_selection,
            instance=context.instance,
            cursor=cursor,
            run_tags=run_tags,
        )

        context.update_cursor(updated_cursor.serialize())
        return run_requests

    return _sensor

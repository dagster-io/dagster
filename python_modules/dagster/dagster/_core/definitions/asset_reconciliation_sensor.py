# pylint: disable=anomalous-backslash-in-string

import functools
import itertools
import json
from collections import defaultdict
import pendulum
from heapq import heapify, heappop, heappush
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

import dagster._check as check
from dagster._annotations import experimental
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.storage.pipeline_run import DagsterRun
from dagster._core.storage.tags import PARTITION_NAME_TAG
from dagster._utils.cached_method import cached_method

from .asset_selection import AssetGraph, AssetSelection
from .partition import PartitionsDefinition, PartitionsSubset
from .repository_definition import RepositoryDefinition
from .run_request import RunRequest
from .sensor_definition import DefaultSensorStatus, SensorDefinition
from .utils import check_valid_name

from dagster._utils.calculate_data_time import DataTimeInstanceQueryer

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance
    from dagster._core.storage.event_log.base import EventLogRecord


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
        return self.materialized_or_requested_root_partitions_by_asset_key.get(
            asset_key, asset_graph.get_partitions_def(asset_key).empty_subset()
        ).get_partition_keys_not_in_subset()

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
                if len(asset_graph.get_parents(asset_key)) == 0:
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

        return AssetReconciliationCursor(
            latest_storage_id=latest_storage_id,
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


class ToposortedPriorityQueue:
    """Queue that returns parents before their children"""

    @functools.total_ordering
    class QueueItem(NamedTuple):
        level: int
        asset_partition: AssetKeyPartitionKey

        def __eq__(self, other):
            return self.level == other.level

        def __lt__(self, other):
            return self.level < other.level

    def __init__(self, asset_graph: AssetGraph, items: Iterable[AssetKeyPartitionKey]):
        toposorted_asset_keys = asset_graph.toposort_asset_keys()
        self._toposort_level_by_asset_key = {
            asset_key: i
            for i, asset_keys in enumerate(toposorted_asset_keys)
            for asset_key in asset_keys
        }
        self._heap = [
            ToposortedPriorityQueue.QueueItem(
                self._toposort_level_by_asset_key[asset_partition.asset_key], asset_partition
            )
            for asset_partition in items
        ]
        heapify(self._heap)

    def enqueue(self, asset_partition: AssetKeyPartitionKey) -> None:
        priority = self._toposort_level_by_asset_key[asset_partition.asset_key]
        heappush(self._heap, ToposortedPriorityQueue.QueueItem(priority, asset_partition))

    def dequeue(self) -> AssetKeyPartitionKey:
        return heappop(self._heap).asset_partition

    def __len__(self) -> int:
        return len(self._heap)


def find_stale_candidates(
    instance_queryer: DataTimeInstanceQueryer,
    cursor: AssetReconciliationCursor,
    target_asset_selection: AssetSelection,
    asset_graph: AssetGraph,
) -> Tuple[AbstractSet[AssetKeyPartitionKey], Optional[int]]:
    """
    Cheaply identifies a set of reconciliation candidates, which can then be vetted with more
    heavyweight logic after.

    The contract of this function is:
    - Every asset (partition) that requires reconciliation must either be one of the returned
        candidates or a descendant of one of the returned candidates.
    - Not every returned candidate must require reconciliation.

    Returns:
        - A set of reconciliation candidates.
        - The latest observed storage_id across all relevant assets. Can be used to avoid scanning
            the same events the next time this function is called.
    """

    stale_candidates: Set[AssetKeyPartitionKey] = set()
    latest_storage_id = None

    target_asset_keys = target_asset_selection.resolve(asset_graph)

    for asset_key, record in instance_queryer.get_latest_materialization_records_by_key(
        target_asset_selection.upstream(depth=1).resolve(asset_graph),
        cursor.latest_storage_id,
    ).items():
        # The children of updated assets might now be unreconciled:
        for child in asset_graph.get_children_partitions(asset_key, record.partition_key):
            if (
                child.asset_key in target_asset_keys
                and not instance_queryer.is_asset_partition_in_run(record.run_id, child)
            ):
                stale_candidates.add(child)

        if latest_storage_id is None or record.storage_id > latest_storage_id:
            latest_storage_id = record.storage_id

    return (stale_candidates, latest_storage_id)


def find_never_materialized_or_requested_root_asset_partitions(
    instance_queryer: DataTimeInstanceQueryer,
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


def determine_asset_partitions_to_reconcile(
    instance_queryer: DataTimeInstanceQueryer,
    cursor: AssetReconciliationCursor,
    target_asset_selection: AssetSelection,
    asset_graph: AssetGraph,
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

    stale_candidates, latest_storage_id = find_stale_candidates(
        instance_queryer=instance_queryer,
        cursor=cursor,
        target_asset_selection=target_asset_selection,
        asset_graph=asset_graph,
    )
    target_asset_keys = target_asset_selection.resolve(asset_graph)

    to_reconcile: Set[AssetKeyPartitionKey] = set()
    all_candidates = set(itertools.chain(never_materialized_or_requested_roots, stale_candidates))

    # invariant: we never consider a candidate before considering its ancestors
    candidates_queue = ToposortedPriorityQueue(asset_graph, all_candidates)

    while len(candidates_queue) > 0:
        candidate = candidates_queue.dequeue()

        if (
            # all of its parents reconciled first
            all(
                (
                    (
                        parent in to_reconcile
                        # if they don't have the same partitioning, then we can't launch a run that
                        # targets both, so we need to wait until the parent is reconciled before
                        # launching a run for the child
                        and asset_graph.have_same_partitioning(
                            parent.asset_key, candidate.asset_key
                        )
                    )
                    or (
                        instance_queryer.is_reconciled(
                            asset_partition=parent, asset_graph=asset_graph
                        )
                    )
                )
                for parent in asset_graph.get_parents_partitions(
                    candidate.asset_key, candidate.partition_key
                )
            )
            and not instance_queryer.is_reconciled(
                asset_partition=candidate, asset_graph=asset_graph
            )
        ):
            to_reconcile.add(candidate)
            for child in asset_graph.get_children_partitions(
                candidate.asset_key, candidate.partition_key
            ):
                if (
                    child.asset_key in target_asset_keys
                    and child not in all_candidates
                    and asset_graph.have_same_partitioning(child.asset_key, candidate.asset_key)
                ):
                    candidates_queue.enqueue(child)
                    all_candidates.add(child)

    return (
        to_reconcile,
        newly_materialized_root_asset_keys,
        newly_materialized_root_partitions_by_asset_key,
        latest_storage_id,
    )


def determine_asset_partitions_to_reconcile_for_freshness(
    instance_queryer: DataTimeInstanceQueryer,
    asset_graph: AssetGraph,
    freshness_policies_by_key: Mapping[AssetKey, FreshnessPolicy],
) -> Tuple[Set[AssetKey], Set[AssetKeyPartitionKey]]:
    """Returns a set of AssetKeyPartitionKeys to materialize in order to abide by the given
    FreshnessPolicies, as well as a set of AssetKeyPartitionKeys which will be materialized at
    some point within the plan window.

    Attempts to minimize the total number of asset executions.
    """

    # exit early
    if not freshness_policies_by_key:
        return set(), set()

    # look within a 12-hour time window to combine future runs together
    current_time = pendulum.now(tz=pendulum.UTC)
    plan_window_start = current_time
    plan_window_end = plan_window_start + pendulum.duration(hours=12)

    # a dictionary mapping each asset to a set of constraints that must be satisfied about the data
    # times of its upstream assets
    constraints_by_key = defaultdict(set)

    # for each asset with a FreshnessPolicy, get all unsolved constraints for the given time window
    for key, freshness_policy in freshness_policies_by_key.items():
        upstream_keys = asset_graph.get_roots(key)
        latest_record = instance_queryer.get_latest_materialization_record(key)
        used_data_times = (
            instance_queryer.get_used_data_times_for_record(
                asset_graph=asset_graph, record=latest_record, upstream_keys=upstream_keys
            )
            if latest_record is not None
            else {}
        )
        available_data_times = {upstream_key: plan_window_start for upstream_key in upstream_keys}
        constraints_by_key[key] = freshness_policy.constraints_for_time_window(
            window_start=plan_window_start,
            window_end=plan_window_end,
            used_data_times=used_data_times,
            available_data_times=available_data_times,
        )

    toposorted_assets = asset_graph.toposort_asset_keys()
    # propagate constraints upwards through the graph
    #
    # we ignore whether or not the constraint we're propagating corresponds to an asset which
    # is actually upstream of the asset we're operating on, as we'll filter those invalid
    # constraints out in the next step, and it's expensive to calculate if a given asset is
    # upstream of another asset.
    for level in reversed(toposorted_assets):
        for key in level:
            for upstream_key in asset_graph.get_parents(key):
                # pass along all of your constraints to your parents
                constraints_by_key[upstream_key] |= constraints_by_key[key]

    # now we have a full set of constraints, we can find solutions for them as we move back down
    to_materialize: Set[AssetKeyPartitionKey] = set()
    eventually_materialize: Set[AssetKeyPartitionKey] = set()
    expected_data_times_by_key: Dict[Dict[AssetKey, float]] = defaultdict(dict)
    for level in toposorted_assets:
        for key in level:
            # no need to evaluate this key, as it is not involved in any constraints
            constraints = constraints_by_key[key]
            if not constraints:
                continue

            # check to find if this asset is currently being materialized by a run, and if so, which
            # other assets are being materialized in that run
            (
                current_run_data_time,
                currently_materializing,
            ) = instance_queryer.get_in_progress_run_time_and_planned_materializations(key)

            expected_data_times = {key: current_time}

            # get the expected data time for each upstream asset key if you were to run this asset on
            # this tick
            for upstream_key in asset_graph.get_parents(key):
                for upstream_upstream_key, expected_data_time in expected_data_times_by_key[
                    upstream_key
                ].items():
                    # take the minimum data time from each of your parents
                    expected_data_times[upstream_upstream_key] = min(
                        expected_data_times.get(upstream_upstream_key, expected_data_time),
                        expected_data_time,
                    )

            relevant_upstream_keys = set()
            for constraint in constraints:
                if constraint.asset_key in expected_data_times:
                    relevant_upstream_keys.add(constraint.asset_key)

            # calculate the data time for this record in relation to the upstream keys which are
            # set to be updated this tick and are involved in some constraint
            latest_record = instance_queryer.get_latest_materialization_record(key)
            current_data_times = (
                instance_queryer.get_used_data_times_for_record(
                    asset_graph=asset_graph,
                    upstream_keys=relevant_upstream_keys,
                    record=latest_record,
                )
                if latest_record is not None
                else {}
            )

            # figure out a range of times that you could kick off an execution to solve the most
            # pressing constraint, alongside a maximum number of additional constraints
            execution_window_start = None
            execution_window_end = None
            for constraint in sorted(constraints_by_key[key], key=lambda c: c.required_by_time):
                current_data_time = current_data_times.get(constraint.asset_key)

                if not (
                    # this constraint is irrelevant, as it is satisfied by the current data time
                    (
                        current_data_time is not None
                        and current_data_time > constraint.required_data_time
                    )
                    # this constraint is irrelevant, as a currently-executing run will satisfy it
                    or (
                        constraint.asset_key in currently_materializing
                        # if the run hasn't started yet, assume it'll get data from the current time
                        and (current_run_data_time or plan_window_start) > required_data_time
                    )
                    # this constraint is irrelevant, as it does not correspond to an asset which is
                    # directly upstream of this asset, nor to an asset which is transitively
                    # upstream of this asset and will be materialized this tick
                    or constraint.asset_key not in expected_data_times
                ):
                    if execution_window_start is None:
                        execution_window_start = constraint.required_data_time
                    if execution_window_end is None:
                        execution_window_end = constraint.required_by_time

                    # you can solve this constraint within the existing execution window
                    if constraint.required_data_time < execution_window_end:
                        execution_window_start = max(
                            execution_window_start,
                            constraint.required_data_time,
                        )
                        execution_window_end = min(
                            execution_window_end,
                            constraint.required_by_time,
                        )

            # now that you have an execution window that will allow you to solve a maximum number of
            # constraints at once, kick off a run at the beginning of that time window to give it
            # maximum time to complete
            if execution_window_start is not None and execution_window_start <= current_time:
                to_materialize.add(AssetKeyPartitionKey(key, None))
                # only propogate these expected data times if you plan on kicking off a run
                expected_data_times_by_key[key] = expected_data_times
            else:
                # this key is planned to be updated within the plan window
                if execution_window_start is not None:
                    eventually_materialize.add(AssetKeyPartitionKey(key, None))
                # otherwise, the expected data time will be the current one
                expected_data_times_by_key[key] = current_data_times

    return to_materialize, eventually_materialize


def reconcile(
    repository_def: RepositoryDefinition,
    asset_selection: AssetSelection,
    instance: "DagsterInstance",
    cursor: AssetReconciliationCursor,
    run_tags: Optional[Mapping[str, str]],
):
    from dagster._utils.calculate_data_time import DataTimeInstanceQueryer

    instance_queryer = DataTimeInstanceQueryer(instance=instance)
    asset_graph = repository_def.asset_graph

    (
        asset_partitions_to_reconcile_for_freshness,
        eventual_asset_partitions_to_reconcile_for_freshness,
    ) = determine_asset_partitions_to_reconcile_for_freshness(
        instance_queryer=instance_queryer,
        asset_graph=asset_graph,
        freshness_policies_by_key={
            key: assets_def.freshness_policies_by_key[key]
            for key, assets_def in repository_def._assets_defs_by_key.items()
            if assets_def.freshness_policies_by_key.get(key) is not None
        },
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
    )

    assets_to_reconcile_by_partitions_def_partition_key: Mapping[
        Tuple[Optional[PartitionsDefinition], Optional[str]], Set[AssetKey]
    ] = defaultdict(set)

    for asset_partition in (
        asset_partitions_to_reconcile | asset_partitions_to_reconcile_for_freshness
    ):
        # defer materializing the asset now if it will be materialized later
        if asset_partition in eventual_asset_partitions_to_reconcile_for_freshness:
            continue
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

    return run_requests, cursor.with_updates(
        latest_storage_id=latest_storage_id,
        run_requests=run_requests,
        asset_graph=repository_def.asset_graph,
        newly_materialized_root_asset_keys=newly_materialized_root_asset_keys,
        newly_materialized_root_partitions_by_asset_key=newly_materialized_root_partitions_by_asset_key,
    )


@experimental
def build_asset_reconciliation_sensor(
    asset_selection: AssetSelection,
    name: str = "asset_reconciliation_sensor",
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
    run_tags: Optional[Mapping[str, str]] = None,
) -> SensorDefinition:
    """Constructs a sensor that will monitor the provided assets and launch materializations to
    "reconcile" them.

    An asset is considered "unreconciled" if any of:
    - This sensor has never tried to materialize it and it has never been materialized.
    - Any of its parents have been materialized more recently than it has.
    - Any of its parents are unreconciled.

    The sensor won't try to reconcile any assets before their parents are reconciled.

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
        If you have the following asset graph:

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
    """
    check_valid_name(name)
    check.opt_dict_param(run_tags, "run_tags", key_type=str, value_type=str)

    def sensor_fn(context):
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

    return SensorDefinition(
        evaluation_fn=sensor_fn,
        name=name,
        asset_selection=asset_selection,
        minimum_interval_seconds=minimum_interval_seconds,
        description=description,
        default_status=default_status,
    )

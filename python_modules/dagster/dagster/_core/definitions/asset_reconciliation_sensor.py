# pylint: disable=anomalous-backslash-in-string

import functools
import itertools
import json
from collections import defaultdict
from heapq import heapify, heappop, heappush
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
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.storage.pipeline_run import DagsterRun
from dagster._core.storage.tags import PARTITION_NAME_TAG
from dagster._utils.cached_method import cached_method

from .asset_selection import AssetGraph, AssetSelection
from .partition import PartitionsDefinition
from .partitions_subset import PartitionsSubset
from .repository_definition import RepositoryDefinition
from .run_request import RunRequest
from .sensor_definition import DefaultSensorStatus, SensorDefinition
from .utils import check_valid_name

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

    def get_never_requested_never_materialized_partitions(self, asset_key, asset_graph):
        return self.materialized_or_requested_root_partitions_by_asset_key.get(
            asset_key, PartitionsSubset(asset_graph.get_partitions_def(asset_key))
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
                prior_materialized_partitions = PartitionsSubset(
                    partitions_def=asset_graph.get_partitions_def(asset_key),
                )

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
    def from_serialized(cls, cursor: str) -> "AssetReconciliationCursor":
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
            materialized_or_requested_root_partitions_by_asset_key[
                key
            ] = PartitionsSubset.from_serialized(
                serialized_subset, cast(PartitionsDefinition, asset_graph.get_partitions_def(key))
            )
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


class TickInstanceQueryer:
    """Allows caching queries to the instance within a tick."""

    def __init__(self, instance: "DagsterInstance"):
        self._instance = instance

        self._latest_materialization_record_cache: Dict[AssetKeyPartitionKey, "EventLogRecord"] = {}
        # if we try to fetch the latest materialization record after a given cursor and don't find
        # anything, we can keep track of that fact, so that the next time try to fetch the latest
        # materialization record for a >= cursor, we don't need to query the instance
        self._no_materializations_after_cursor_cache: Dict[AssetKeyPartitionKey, int] = {}

    def is_asset_partition_in_run(self, run_id: str, asset_partition: AssetKeyPartitionKey) -> bool:
        run = self._get_run_by_id(run_id=run_id)
        if not run:
            check.failed("")

        if run.tags.get(PARTITION_NAME_TAG) != asset_partition.partition_key:
            return False

        if run.asset_selection:
            return asset_partition.asset_key in run.asset_selection
        else:
            return asset_partition.asset_key in self._get_planned_materializations_for_run(
                run_id=run_id
            )

    @cached_method
    def _get_run_by_id(self, run_id: str) -> Optional[DagsterRun]:
        return self._instance.get_run_by_id(run_id)

    @cached_method
    def _get_planned_materializations_for_run(self, run_id: str) -> AbstractSet[AssetKey]:
        from dagster._core.events import DagsterEventType

        materializations_planned = self._instance.get_records_for_run(
            run_id=run_id,
            of_type=DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
        ).records
        return set(cast(AssetKey, record.asset_key) for record in materializations_planned)

    def get_latest_materialization_record(
        self, asset_partition: AssetKeyPartitionKey, after_cursor: Optional[int]
    ) -> Optional["EventLogRecord"]:
        from dagster._core.events import DagsterEventType
        from dagster._core.storage.event_log.base import EventRecordsFilter

        if asset_partition in self._latest_materialization_record_cache:
            cached_record = self._latest_materialization_record_cache[asset_partition]
            if after_cursor is None or after_cursor < cached_record.storage_id:
                return cached_record
            else:
                return None
        elif asset_partition in self._no_materializations_after_cursor_cache:
            if (
                after_cursor is not None
                and after_cursor >= self._no_materializations_after_cursor_cache[asset_partition]
            ):
                return None

        materialization_records = self._instance.get_event_records(
            EventRecordsFilter(
                event_type=DagsterEventType.ASSET_MATERIALIZATION,
                asset_key=asset_partition.asset_key,
                asset_partitions=[asset_partition.partition_key]
                if asset_partition.partition_key
                else None,
                after_cursor=after_cursor,
            ),
            ascending=False,
            limit=1,
        )

        if materialization_records:
            record = next(iter(materialization_records))
            self._latest_materialization_record_cache[asset_partition] = record
            return record
        else:
            if after_cursor is not None:
                self._no_materializations_after_cursor_cache[asset_partition] = min(
                    after_cursor,
                    self._no_materializations_after_cursor_cache.get(asset_partition, after_cursor),
                )
            return None

    def get_latest_materialization_records_by_key(
        self, asset_keys: Iterable[AssetKey], cursor: Optional[int]
    ) -> Mapping[AssetKey, "EventLogRecord"]:
        """
        Only returns entries for assets that have been materialized since the cursor.
        """
        result: Dict[AssetKey, "EventLogRecord"] = {}

        for asset_key in asset_keys:
            latest_record = self.get_latest_materialization_record(
                AssetKeyPartitionKey(asset_key), cursor
            )
            if latest_record is not None:
                result[asset_key] = latest_record

        return result

    @cached_method
    def is_reconciled(
        self,
        asset_partition: AssetKeyPartitionKey,
        asset_graph: AssetGraph,
    ) -> bool:
        """
        An asset (partition) is considered unreconciled if any of:
        - It has never been materialized
        - One of its parents has been updated more recently than it has
        - One of its parents is unreconciled
        """
        latest_materialization_record = self.get_latest_materialization_record(
            asset_partition, None
        )

        if latest_materialization_record is None:
            return False

        for parent in asset_graph.get_parents_partitions(
            asset_partition.asset_key, asset_partition.partition_key
        ):
            if (
                self.get_latest_materialization_record(
                    parent, after_cursor=latest_materialization_record.storage_id
                )
                is not None
            ):
                return False

            if not self.is_reconciled(asset_partition=parent, asset_graph=asset_graph):
                return False

        return True


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
    instance_queryer: TickInstanceQueryer,
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
    instance_queryer: TickInstanceQueryer,
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
                    newly_materialized_root_asset_keys.add(asset)
                else:
                    never_materialized_or_requested.add(asset)

    return (
        never_materialized_or_requested,
        newly_materialized_root_asset_keys,
        newly_materialized_root_partitions_by_asset_key,
    )


def determine_asset_partitions_to_reconcile(
    instance_queryer: TickInstanceQueryer,
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


def reconcile(
    repository_def: RepositoryDefinition,
    asset_selection: AssetSelection,
    instance: "DagsterInstance",
    cursor: AssetReconciliationCursor,
    run_tags: Optional[Mapping[str, str]],
):
    instance_queryer = TickInstanceQueryer(instance=instance)
    asset_graph = repository_def.asset_graph

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

    for asset_partition in asset_partitions_to_reconcile:
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
            AssetReconciliationCursor.from_serialized(context.cursor)
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

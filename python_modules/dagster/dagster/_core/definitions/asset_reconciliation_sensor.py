# pylint: disable=anomalous-backslash-in-string

import functools
import itertools
import json
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
from dagster._core.definitions.events import AssetKey
from dagster._core.storage.pipeline_run import DagsterRun
from dagster._utils.cached_method import cached_method

from .asset_selection import AssetGraph, AssetSelection
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
        materialized_or_requested_root_asset_keys: Every entry is an asset with no
            parents that has been requested by this sensor or has been materialized (even if not by
            this sensor).
    """

    latest_storage_id: Optional[int]
    materialized_or_requested_root_asset_keys: AbstractSet[AssetKey]

    def was_previously_materialized_or_requested(self, asset_key: AssetKey) -> bool:
        return asset_key in self.materialized_or_requested_root_asset_keys

    def with_updates(
        self,
        latest_storage_id: Optional[int],
        run_requests: Sequence[RunRequest],
        newly_materialized_root_asset_keys: AbstractSet[AssetKey],
        asset_graph: AssetGraph,
    ) -> "AssetReconciliationCursor":
        """
        Returns a cursor that represents this cursor plus the updates that have happened within the
        tick.
        """
        requested_root_assets: Set[AssetKey] = set()

        for run_request in run_requests:
            for asset_key in cast(Iterable[AssetKey], run_request.asset_selection):
                if len(asset_graph.get_parents(asset_key)) == 0:
                    requested_root_assets.add(asset_key)

        result_materialized_or_requested_root_asset_keys = (
            self.materialized_or_requested_root_asset_keys
            | newly_materialized_root_asset_keys
            | requested_root_assets
        )

        return AssetReconciliationCursor(
            latest_storage_id=latest_storage_id,
            materialized_or_requested_root_asset_keys=result_materialized_or_requested_root_asset_keys,
        )

    @classmethod
    def empty(cls) -> "AssetReconciliationCursor":
        return AssetReconciliationCursor(
            latest_storage_id=None,
            materialized_or_requested_root_asset_keys=set(),
        )

    @classmethod
    def from_serialized(cls, cursor: str) -> "AssetReconciliationCursor":
        (
            latest_storage_id,
            serialized_materialized_or_requested_root_asset_keys,
        ) = json.loads(cursor)
        return cls(
            latest_storage_id=latest_storage_id,
            materialized_or_requested_root_asset_keys={
                AssetKey.from_user_string(key_str)
                for key_str in serialized_materialized_or_requested_root_asset_keys
            },
        )

    def serialize(self) -> str:
        serialized = json.dumps(
            (
                self.latest_storage_id,
                [key.to_user_string() for key in self.materialized_or_requested_root_asset_keys],
            )
        )
        return serialized


class TickInstanceQueryer:
    """Allows caching queries to the instance within a tick."""

    def __init__(self, instance: "DagsterInstance"):
        self._instance = instance

        self._latest_materialization_record_cache: Dict[AssetKey, "EventLogRecord"] = {}
        # if we try to fetch the latest materialization record after a given cursor and don't find
        # anything, we can keep track of that fact, so that the next time try to fetch the latest
        # materialization record for a >= cursor, we don't need to query the instance
        self._no_materializations_after_cursor_cache: Dict[AssetKey, int] = {}

    def is_asset_in_run(self, run_id: str, asset_key: AssetKey) -> bool:
        run = self._get_run_by_id(run_id=run_id)
        if not run:
            check.failed("")

        if run.asset_selection:
            return asset_key in run.asset_selection
        else:
            return asset_key in self._get_planned_materializations_for_run(run_id=run_id)

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
        self, asset_key: AssetKey, after_cursor: Optional[int]
    ) -> Optional["EventLogRecord"]:
        from dagster._core.events import DagsterEventType
        from dagster._core.storage.event_log.base import EventRecordsFilter

        if asset_key in self._latest_materialization_record_cache:
            cached_record = self._latest_materialization_record_cache[asset_key]
            if after_cursor is None or after_cursor < cached_record.storage_id:
                return cached_record
            else:
                return None
        elif asset_key in self._no_materializations_after_cursor_cache:
            if (
                after_cursor is not None
                and after_cursor >= self._no_materializations_after_cursor_cache[asset_key]
            ):
                return None

        materialization_records = self._instance.get_event_records(
            EventRecordsFilter(
                event_type=DagsterEventType.ASSET_MATERIALIZATION,
                asset_key=asset_key,
                after_cursor=after_cursor,
            ),
            ascending=False,
            limit=1,
        )

        if materialization_records:
            record = next(iter(materialization_records))
            self._latest_materialization_record_cache[asset_key] = record
            return record
        else:
            if after_cursor is not None:
                self._no_materializations_after_cursor_cache[asset_key] = min(
                    after_cursor,
                    self._no_materializations_after_cursor_cache.get(asset_key, after_cursor),
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
            latest_record = self.get_latest_materialization_record(asset_key, cursor)
            if latest_record is not None:
                result[asset_key] = latest_record

        return result

    @cached_method
    def is_reconciled(self, asset_key: AssetKey, asset_graph: AssetGraph) -> bool:
        """
        An asset is considered unreconciled if any of:
        - It has never been materialized
        - One of its parents has been updated more recently than it has
        - One of its parents is unreconciled
        """
        latest_materialization_record = self.get_latest_materialization_record(asset_key, None)

        if latest_materialization_record is None:
            return False

        for parent in asset_graph.get_parents(asset_key):
            if (
                self.get_latest_materialization_record(
                    parent, after_cursor=latest_materialization_record.storage_id
                )
                is not None
            ):
                return False

            if not self.is_reconciled(asset_key=parent, asset_graph=asset_graph):
                return False

        return True


class ToposortedPriorityQueue:
    """Queue that returns parents before their children"""

    @functools.total_ordering
    class QueueItem(NamedTuple):
        level: int
        asset_key: AssetKey

        def __eq__(self, other):
            return self.level == other.level

        def __lt__(self, other):
            return self.level < other.level

    def __init__(self, asset_graph: AssetGraph, items: Iterable[AssetKey]):
        toposorted_asset_keys = asset_graph.toposort_asset_keys()
        self._toposort_level_by_asset_key = {
            asset_key: i
            for i, asset_keys in enumerate(toposorted_asset_keys)
            for asset_key in asset_keys
        }
        self._heap = [
            ToposortedPriorityQueue.QueueItem(
                self._toposort_level_by_asset_key[asset_key], asset_key
            )
            for asset_key in items
        ]
        heapify(self._heap)

    def enqueue(self, asset_key: AssetKey) -> None:
        priority = self._toposort_level_by_asset_key[asset_key]
        heappush(self._heap, ToposortedPriorityQueue.QueueItem(priority, asset_key))

    def dequeue(self) -> AssetKey:
        return heappop(self._heap).asset_key

    def __len__(self) -> int:
        return len(self._heap)


def find_stale_candidates(
    instance_queryer: TickInstanceQueryer,
    cursor: AssetReconciliationCursor,
    target_asset_selection: AssetSelection,
    asset_graph: AssetGraph,
) -> Tuple[AbstractSet[AssetKey], Optional[int]]:
    """
    Cheaply identifies a set of reconciliation candidates, which can then be vetted with more
    heavyweight logic after.

    The contract of this function is:
    - Every asset that requires reconciliation must either be one of the returned
        candidates or a descendant of one of the returned candidates.
    - Not every returned candidate must require reconciliation.

    Returns:
        - A set of reconciliation candidates.
        - The latest observed storage_id across all relevant assets. Can be used to avoid scanning
            the same events the next time this function is called.
    """

    stale_candidates: Set[AssetKey] = set()
    latest_storage_id = None

    target_asset_keys = target_asset_selection.resolve(asset_graph)

    for asset_key, record in instance_queryer.get_latest_materialization_records_by_key(
        target_asset_selection.upstream(depth=1).resolve(asset_graph),
        cursor.latest_storage_id,
    ).items():
        # The children of updated assets might now be unreconciled:
        for child in asset_graph.get_children(asset_key):
            if child in target_asset_keys and not instance_queryer.is_asset_in_run(
                record.run_id, child
            ):
                stale_candidates.add(child)

        if latest_storage_id is None or record.storage_id > latest_storage_id:
            latest_storage_id = record.storage_id

    return (stale_candidates, latest_storage_id)


def find_never_materialized_or_requested_root_assets(
    instance_queryer: TickInstanceQueryer,
    cursor: AssetReconciliationCursor,
    target_asset_selection: AssetSelection,
    asset_graph: AssetGraph,
) -> Tuple[Iterable[AssetKey], AbstractSet[AssetKey]]:
    """Finds assets that have never been materialized or requested and that have no
    parents.

    Returns:
    - Assets that have never been materialized or requested.
    - Assets that had never been materialized or requested up to the previous cursor
        but are now materialized.
    """
    never_materialized_or_requested = set()
    newly_materialized_root_asset_keys = set()

    for asset_key in (target_asset_selection & AssetSelection.all().sources()).resolve(asset_graph):
        if not cursor.was_previously_materialized_or_requested(asset_key):
            if instance_queryer.get_latest_materialization_record(asset_key, None):
                newly_materialized_root_asset_keys.add(asset_key)
            else:
                never_materialized_or_requested.add(asset_key)

    return (
        never_materialized_or_requested,
        newly_materialized_root_asset_keys,
    )


def determine_assets_to_reconcile(
    instance_queryer: TickInstanceQueryer,
    cursor: AssetReconciliationCursor,
    target_asset_selection: AssetSelection,
    asset_graph: AssetGraph,
) -> Tuple[AbstractSet[AssetKey], AbstractSet[AssetKey], Optional[int],]:
    (
        never_materialized_or_requested_roots,
        newly_materialized_root_asset_keys,
    ) = find_never_materialized_or_requested_root_assets(
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

    to_reconcile: Set[AssetKey] = set()
    all_candidates = set(itertools.chain(never_materialized_or_requested_roots, stale_candidates))

    # invariant: we never consider a candidate before considering its ancestors
    candidates_queue = ToposortedPriorityQueue(asset_graph, all_candidates)

    while len(candidates_queue) > 0:
        candidate = candidates_queue.dequeue()

        if (
            # all of its parents reconciled first
            all(
                (
                    (parent in to_reconcile)
                    or (instance_queryer.is_reconciled(asset_key=parent, asset_graph=asset_graph))
                )
                for parent in asset_graph.get_parents(candidate)
            )
            and not instance_queryer.is_reconciled(asset_key=candidate, asset_graph=asset_graph)
        ):
            to_reconcile.add(candidate)
            for child in asset_graph.get_children(candidate):
                if child in target_asset_keys and child not in all_candidates:
                    candidates_queue.enqueue(child)
                    all_candidates.add(child)

    return (
        to_reconcile,
        newly_materialized_root_asset_keys,
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
        assets_to_reconcile,
        newly_materialized_root_asset_keys,
        latest_storage_id,
    ) = determine_assets_to_reconcile(
        instance_queryer=instance_queryer,
        asset_graph=asset_graph,
        cursor=cursor,
        target_asset_selection=asset_selection,
    )

    if assets_to_reconcile:
        run_requests = [RunRequest(asset_selection=list(assets_to_reconcile), tags=run_tags)]
    else:
        run_requests = []

    return run_requests, cursor.with_updates(
        latest_storage_id=latest_storage_id,
        run_requests=run_requests,
        asset_graph=repository_def.asset_graph,
        newly_materialized_root_asset_keys=newly_materialized_root_asset_keys,
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

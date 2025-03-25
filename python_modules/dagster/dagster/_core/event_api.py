import base64
from collections.abc import Mapping, Sequence
from datetime import datetime
from enum import Enum
from typing import Callable, Literal, NamedTuple, Optional, Union

from dagster_shared.seven import json
from typing_extensions import TypeAlias

import dagster._check as check
from dagster._annotations import PublicAttr
from dagster._core.definitions.events import AssetKey, AssetMaterialization, AssetObservation
from dagster._core.events import EVENT_TYPE_TO_PIPELINE_RUN_STATUS, DagsterEventType
from dagster._core.events.log import EventLogEntry
from dagster._serdes import whitelist_for_serdes

EventHandlerFn: TypeAlias = Callable[[EventLogEntry, str], None]


class EventLogCursorType(Enum):
    OFFSET = "OFFSET"
    STORAGE_ID = "STORAGE_ID"


class EventLogCursor(NamedTuple):
    """Representation of an event record cursor, keeping track of the log query state."""

    cursor_type: EventLogCursorType
    value: int

    def is_offset_cursor(self) -> bool:
        return self.cursor_type == EventLogCursorType.OFFSET

    def is_id_cursor(self) -> bool:
        return self.cursor_type == EventLogCursorType.STORAGE_ID

    def offset(self) -> int:
        check.invariant(self.cursor_type == EventLogCursorType.OFFSET)
        return max(0, int(self.value))

    def storage_id(self) -> int:
        check.invariant(self.cursor_type == EventLogCursorType.STORAGE_ID)
        return int(self.value)

    def __str__(self) -> str:
        return self.to_string()

    def to_string(self) -> str:
        raw = json.dumps({"type": self.cursor_type.value, "value": self.value})
        return base64.b64encode(bytes(raw, encoding="utf-8")).decode("utf-8")

    @staticmethod
    def parse(cursor_str: str) -> "EventLogCursor":
        raw = json.loads(base64.b64decode(cursor_str).decode("utf-8"))
        return EventLogCursor(EventLogCursorType(raw["type"]), raw["value"])

    @staticmethod
    def from_offset(offset: int) -> "EventLogCursor":
        return EventLogCursor(EventLogCursorType.OFFSET, offset)

    @staticmethod
    def from_storage_id(storage_id: int) -> "EventLogCursor":
        return EventLogCursor(EventLogCursorType.STORAGE_ID, storage_id)


class RunShardedEventsCursor(NamedTuple):
    """Pairs an id-based event log cursor with a timestamp-based run cursor, for improved
    performance on run-sharded event log storages (e.g. the default SqliteEventLogStorage). For
    run-sharded storages, the id field is ignored, since they may not be unique across shards.
    """

    id: int
    run_updated_after: datetime


RunStatusChangeEventType: TypeAlias = Literal[
    DagsterEventType.RUN_START,
    DagsterEventType.RUN_SUCCESS,
    DagsterEventType.RUN_FAILURE,
    DagsterEventType.RUN_ENQUEUED,
    DagsterEventType.RUN_STARTING,
    DagsterEventType.RUN_CANCELING,
    DagsterEventType.RUN_CANCELED,
]
AssetEventType: TypeAlias = Literal[
    DagsterEventType.ASSET_MATERIALIZATION,
    DagsterEventType.ASSET_OBSERVATION,
    DagsterEventType.ASSET_MATERIALIZATION_PLANNED,
    DagsterEventType.ASSET_FAILED_TO_MATERIALIZE,
]

EventCursor: TypeAlias = Union[int, RunShardedEventsCursor]


@whitelist_for_serdes
class EventLogRecord(NamedTuple):
    """Internal representation of an event record, as stored in a
    :py:class:`~dagster._core.storage.event_log.EventLogStorage`.

    Users should not instantiate this class directly.
    """

    storage_id: PublicAttr[int]
    event_log_entry: PublicAttr[EventLogEntry]

    @property
    def run_id(self) -> str:
        return self.event_log_entry.run_id

    @property
    def timestamp(self) -> float:
        return self.event_log_entry.timestamp

    @property
    def asset_key(self) -> Optional[AssetKey]:
        dagster_event = self.event_log_entry.dagster_event
        if dagster_event:
            return dagster_event.asset_key

        return None

    @property
    def partition_key(self) -> Optional[str]:
        dagster_event = self.event_log_entry.dagster_event
        if dagster_event:
            return dagster_event.partition

        return None

    @property
    def asset_materialization(self) -> Optional[AssetMaterialization]:
        return self.event_log_entry.asset_materialization

    @property
    def asset_observation(self) -> Optional[AssetObservation]:
        return self.event_log_entry.asset_observation

    @property
    def asset_event(self) -> Optional[Union[AssetMaterialization, AssetObservation]]:
        return self.asset_materialization or self.asset_observation

    @property
    def event_type(self) -> DagsterEventType:
        return check.not_none(
            self.event_log_entry.dagster_event,
            "Expected dagster_event property to be present if calling the event_type property",
        ).event_type


class EventRecordsResult(NamedTuple):
    """Return value for a query fetching event records from the instance.  Contains a list of event
    records, a cursor string, and a boolean indicating whether there are more records to fetch.
    """

    records: Sequence[EventLogRecord]
    cursor: str
    has_more: bool


@whitelist_for_serdes
class EventRecordsFilter(
    NamedTuple(
        "_EventRecordsFilter",
        [
            ("event_type", DagsterEventType),
            ("asset_key", Optional[AssetKey]),
            ("asset_partitions", Optional[Sequence[str]]),
            ("after_cursor", Optional[EventCursor]),
            ("before_cursor", Optional[EventCursor]),
            ("after_timestamp", Optional[float]),
            ("before_timestamp", Optional[float]),
            ("storage_ids", Optional[Sequence[int]]),
        ],
    )
):
    """Defines a set of filter fields for fetching a set of event log entries or event log records.

    Args:
        event_type (DagsterEventType): Filter argument for dagster event type
        asset_key (Optional[AssetKey]): Asset key for which to get asset materialization event
            entries / records.
        asset_partitions (Optional[List[str]]): Filter parameter such that only asset
            events with a partition value matching one of the provided values.  Only
            valid when the `asset_key` parameter is provided.
        after_cursor (Optional[EventCursor]): Filter parameter such that only
            records with storage_id greater than the provided value are returned. Using a
            run-sharded events cursor will result in a significant performance gain when run against
            a SqliteEventLogStorage implementation (which is run-sharded)
        before_cursor (Optional[EventCursor]): Filter parameter such that
            records with storage_id less than the provided value are returned. Using a run-sharded
            events cursor will result in a significant performance gain when run against
            a SqliteEventLogStorage implementation (which is run-sharded)
        after_timestamp (Optional[float]): Filter parameter such that only event records for
            events with timestamp greater than the provided value are returned.
        before_timestamp (Optional[float]): Filter parameter such that only event records for
            events with timestamp less than the provided value are returned.
    """

    def __new__(
        cls,
        event_type: DagsterEventType,
        asset_key: Optional[AssetKey] = None,
        asset_partitions: Optional[Sequence[str]] = None,
        after_cursor: Optional[EventCursor] = None,
        before_cursor: Optional[EventCursor] = None,
        after_timestamp: Optional[float] = None,
        before_timestamp: Optional[float] = None,
        storage_ids: Optional[Sequence[int]] = None,
    ):
        check.opt_sequence_param(asset_partitions, "asset_partitions", of_type=str)
        check.inst_param(event_type, "event_type", DagsterEventType)

        # type-ignores work around mypy type inference bug
        return super().__new__(
            cls,
            event_type=event_type,
            asset_key=check.opt_inst_param(asset_key, "asset_key", AssetKey),
            asset_partitions=asset_partitions,
            after_cursor=check.opt_inst_param(
                after_cursor, "after_cursor", (int, RunShardedEventsCursor)
            ),
            before_cursor=check.opt_inst_param(
                before_cursor, "before_cursor", (int, RunShardedEventsCursor)
            ),
            after_timestamp=check.opt_float_param(after_timestamp, "after_timestamp"),
            before_timestamp=check.opt_float_param(before_timestamp, "before_timestamp"),
            storage_ids=check.opt_nullable_sequence_param(storage_ids, "storage_ids", of_type=int),
        )

    @staticmethod
    def get_cursor_params(
        cursor: Optional[str] = None, ascending: bool = False
    ) -> tuple[Optional[int], Optional[int]]:
        if not cursor:
            return None, None

        cursor_obj = EventLogCursor.parse(cursor)
        if not cursor_obj.is_id_cursor():
            check.failed(f"Invalid cursor for fetching event records: {cursor}")
        after_cursor = cursor_obj.storage_id() if ascending else None
        before_cursor = cursor_obj.storage_id() if not ascending else None
        return before_cursor, after_cursor

    @property
    def tags(self) -> Optional[Mapping[str, Union[str, Sequence[str]]]]:
        return None


@whitelist_for_serdes
class AssetRecordsFilter(
    NamedTuple(
        "_AssetRecordsFilter",
        [
            ("asset_key", PublicAttr[AssetKey]),
            ("asset_partitions", PublicAttr[Optional[Sequence[str]]]),
            ("after_timestamp", PublicAttr[Optional[float]]),
            ("before_timestamp", PublicAttr[Optional[float]]),
            ("after_storage_id", PublicAttr[Optional[int]]),
            ("before_storage_id", PublicAttr[Optional[int]]),
            ("storage_ids", PublicAttr[Optional[Sequence[int]]]),
        ],
    )
):
    """Defines a set of filter fields for fetching a set of asset event records.

    Args:
        asset_key (Optional[AssetKey]): Asset key for which to get asset event entries / records.
        asset_partitions (Optional[List[str]]): Filter parameter such that only asset
            events with a partition value matching one of the provided values are returned.  Only
            valid when the `asset_key` parameter is provided.
        after_timestamp (Optional[float]): Filter parameter such that only event records for
            events with timestamp greater than the provided value are returned.
        before_timestamp (Optional[float]): Filter parameter such that only event records for
            events with timestamp less than the provided value are returned.
        after_storage_id (Optional[float]): Filter parameter such that only event records for
            events with storage_id greater than the provided value are returned.
        before_storage_id (Optional[float]): Filter parameter such that only event records for
            events with storage_id less than the provided value are returned.
        storage_ids (Optional[Sequence[int]]): Filter parameter such that only event records for
            the given storage ids are returned.
        tags (Optional[Mapping[str, Union[str, Sequence[str]]]]): Filter parameter such that only
            events with the given event tags are returned
    """

    def __new__(
        cls,
        asset_key: AssetKey,
        asset_partitions: Optional[Sequence[str]] = None,
        after_timestamp: Optional[float] = None,
        before_timestamp: Optional[float] = None,
        after_storage_id: Optional[int] = None,
        before_storage_id: Optional[int] = None,
        storage_ids: Optional[Sequence[int]] = None,
    ):
        return super().__new__(
            cls,
            asset_key=check.inst_param(asset_key, "asset_key", AssetKey),
            asset_partitions=check.opt_nullable_sequence_param(
                asset_partitions, "asset_partitions", of_type=str
            ),
            after_timestamp=check.opt_float_param(after_timestamp, "after_timestamp"),
            before_timestamp=check.opt_float_param(before_timestamp, "before_timestamp"),
            after_storage_id=check.opt_int_param(after_storage_id, "after_storage_id"),
            before_storage_id=check.opt_int_param(before_storage_id, "before_storage_id"),
            storage_ids=check.opt_nullable_sequence_param(storage_ids, "storage_ids", of_type=int),
        )

    def to_event_records_filter(
        self, event_type: AssetEventType, cursor: Optional[str] = None, ascending: bool = False
    ) -> EventRecordsFilter:
        before_cursor_storage_id, after_cursor_storage_id = EventRecordsFilter.get_cursor_params(
            cursor, ascending
        )
        if self.before_storage_id and before_cursor_storage_id:
            before_cursor = min(self.before_storage_id, before_cursor_storage_id)
        else:
            before_cursor = (
                before_cursor_storage_id if before_cursor_storage_id else self.before_storage_id
            )
        if self.after_storage_id and after_cursor_storage_id:
            after_cursor = max(self.after_storage_id, after_cursor_storage_id)
        else:
            after_cursor = (
                after_cursor_storage_id if after_cursor_storage_id else self.after_storage_id
            )

        return EventRecordsFilter(
            event_type=event_type,
            asset_key=self.asset_key,
            asset_partitions=self.asset_partitions,
            after_cursor=after_cursor,
            before_cursor=before_cursor,
            after_timestamp=self.after_timestamp,
            before_timestamp=self.before_timestamp,
            storage_ids=self.storage_ids,
        )

    @property
    def tags(self) -> Optional[Mapping[str, Union[str, Sequence[str]]]]:
        return None


@whitelist_for_serdes
class RunStatusChangeRecordsFilter(
    NamedTuple(
        "_RunStatusChangeRecordsFilter",
        [
            ("event_type", PublicAttr[RunStatusChangeEventType]),
            ("after_timestamp", PublicAttr[Optional[float]]),
            ("before_timestamp", PublicAttr[Optional[float]]),
            ("after_storage_id", PublicAttr[Optional[int]]),
            ("before_storage_id", PublicAttr[Optional[int]]),
            ("storage_ids", PublicAttr[Optional[Sequence[int]]]),
            ("job_names", Optional[Sequence[str]]),
        ],
    )
):
    """Defines a set of filter fields for fetching a set of asset event records.

    Args:
        event_type (DagsterEventType): Filter argument for dagster event type
        after_timestamp (Optional[float]): Filter parameter such that only event records for
            events with timestamp greater than the provided value are returned.
        before_timestamp (Optional[float]): Filter parameter such that only event records for
            events with timestamp less than the provided value are returned.
        after_storage_id (Optional[float]): Filter parameter such that only event records for
            events with storage_id greater than the provided value are returned.
        before_storage_id (Optional[float]): Filter parameter such that only event records for
            events with storage_id less than the provided value are returned.
        storage_ids (Optional[Sequence[int]]): Filter parameter such that only event records for
            the given storage ids are returned.
    """

    def __new__(
        cls,
        event_type: RunStatusChangeEventType,
        after_timestamp: Optional[float] = None,
        before_timestamp: Optional[float] = None,
        after_storage_id: Optional[int] = None,
        before_storage_id: Optional[int] = None,
        storage_ids: Optional[Sequence[int]] = None,
        job_names: Optional[Sequence[str]] = None,
    ):
        if event_type not in EVENT_TYPE_TO_PIPELINE_RUN_STATUS:
            check.failed("Invalid event type for run status change event filter")

        return super().__new__(
            cls,
            event_type=check.inst_param(event_type, "event_type", DagsterEventType),
            after_timestamp=check.opt_float_param(after_timestamp, "after_timestamp"),
            before_timestamp=check.opt_float_param(before_timestamp, "before_timestamp"),
            after_storage_id=check.opt_int_param(after_storage_id, "after_storage_id"),
            before_storage_id=check.opt_int_param(before_storage_id, "before_storage_id"),
            storage_ids=check.opt_nullable_sequence_param(storage_ids, "storage_ids", of_type=int),
            job_names=check.opt_nullable_sequence_param(job_names, "job_names", of_type=str),
        )

    def to_event_records_filter_without_job_names(
        self, cursor: Optional[str] = None, ascending: bool = False
    ) -> EventRecordsFilter:
        before_cursor_storage_id, after_cursor_storage_id = EventRecordsFilter.get_cursor_params(
            cursor, ascending
        )
        if self.before_storage_id and before_cursor_storage_id:
            before_cursor = min(self.before_storage_id, before_cursor_storage_id)
        else:
            before_cursor = (
                before_cursor_storage_id if before_cursor_storage_id else self.before_storage_id
            )
        if self.after_storage_id and after_cursor_storage_id:
            after_cursor = max(self.after_storage_id, after_cursor_storage_id)
        else:
            after_cursor = (
                after_cursor_storage_id if after_cursor_storage_id else self.after_storage_id
            )

        return EventRecordsFilter(
            event_type=self.event_type,
            after_cursor=after_cursor,
            before_cursor=before_cursor,
            after_timestamp=self.after_timestamp,
            before_timestamp=self.before_timestamp,
            storage_ids=self.storage_ids,
        )

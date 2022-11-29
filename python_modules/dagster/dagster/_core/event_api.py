from datetime import datetime
from typing import Mapping, NamedTuple, Optional, Sequence, Union

import dagster._check as check
from dagster._annotations import PublicAttr
from dagster._core.definitions.events import AssetKey
from dagster._core.errors import DagsterInvalidInvocationError
from dagster._core.events import DagsterEventType
from dagster._core.events.log import EventLogEntry
from dagster._serdes import whitelist_for_serdes


class RunShardedEventsCursor(NamedTuple):
    """Pairs an id-based event log cursor with a timestamp-based run cursor, for improved
    performance on run-sharded event log storages (e.g. the default SqliteEventLogStorage). For
    run-sharded storages, the id field is ignored, since they may not be unique across shards
    """

    id: int
    run_updated_after: datetime


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


@whitelist_for_serdes
class EventRecordsFilter(
    NamedTuple(
        "_EventRecordsFilter",
        [
            ("event_type", DagsterEventType),
            ("asset_key", Optional[AssetKey]),
            ("asset_partitions", Optional[Sequence[str]]),
            ("after_cursor", Optional[Union[int, RunShardedEventsCursor]]),
            ("before_cursor", Optional[Union[int, RunShardedEventsCursor]]),
            ("after_timestamp", Optional[float]),
            ("before_timestamp", Optional[float]),
            ("storage_ids", Optional[Sequence[int]]),
            ("tags", Optional[Mapping[str, Union[str, Sequence[str]]]]),
        ],
    )
):
    """Defines a set of filter fields for fetching a set of event log entries or event log records.

    Args:
        event_type (DagsterEventType): Filter argument for dagster event type
        asset_key (Optional[AssetKey]): Asset key for which to get asset materialization event
            entries / records.
        asset_partitions (Optional[List[str]]): Filter parameter such that only asset
            materialization events with a partition value matching one of the provided values.  Only
            valid when the `asset_key` parameter is provided.
        after_cursor (Optional[Union[int, RunShardedEventsCursor]]): Filter parameter such that only
            records with storage_id greater than the provided value are returned. Using a
            run-sharded events cursor will result in a significant performance gain when run against
            a SqliteEventLogStorage implementation (which is run-sharded)
        before_cursor (Optional[Union[int, RunShardedEventsCursor]]): Filter parameter such that
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
        after_cursor: Optional[Union[int, RunShardedEventsCursor]] = None,
        before_cursor: Optional[Union[int, RunShardedEventsCursor]] = None,
        after_timestamp: Optional[float] = None,
        before_timestamp: Optional[float] = None,
        storage_ids: Optional[Sequence[int]] = None,
        tags: Optional[Mapping[str, Union[str, Sequence[str]]]] = None,
    ):
        check.opt_sequence_param(asset_partitions, "asset_partitions", of_type=str)
        check.inst_param(event_type, "event_type", DagsterEventType)

        tags = check.opt_mapping_param(tags, "tags", key_type=str)
        if tags and event_type is not DagsterEventType.ASSET_MATERIALIZATION:
            raise DagsterInvalidInvocationError(
                "Can only filter by tags for asset materialization events"
            )

        # type-ignores work around mypy type inference bug
        return super(EventRecordsFilter, cls).__new__(
            cls,
            event_type=event_type,
            asset_key=check.opt_inst_param(asset_key, "asset_key", AssetKey),
            asset_partitions=asset_partitions,
            after_cursor=check.opt_inst_param(  # type: ignore
                after_cursor, "after_cursor", (int, RunShardedEventsCursor)
            ),
            before_cursor=check.opt_inst_param(  # type: ignore
                before_cursor, "before_cursor", (int, RunShardedEventsCursor)
            ),
            after_timestamp=check.opt_float_param(after_timestamp, "after_timestamp"),
            before_timestamp=check.opt_float_param(before_timestamp, "before_timestamp"),
            storage_ids=check.opt_sequence_param(storage_ids, "storage_ids", of_type=int),
            tags=check.opt_mapping_param(tags, "tags", key_type=str),
        )
